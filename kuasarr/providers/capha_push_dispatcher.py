# -*- coding: utf-8 -*-
"""Hintergrund-Dispatcher, der geschützte Pakete an CaptchaSolverr pusht.

Nutzt die neue CaptchaSolverr v1 API (/v1/solve, /v1/status, /v1/result).
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional, Tuple

from kuasarr.providers import push_jobs, shared_state
from kuasarr.providers.captchasolverr_client import (
    CaptchaSolverrClient,
    CaptchaSolverrError,
    ServiceStatus,
    create_captchasolverr_client,
)
from kuasarr.providers.log import info, debug

DEFAULT_PUSH_INTERVAL_SECONDS = 5
ACTIVE_PUSH_STATUSES = {"pending", "sent"}
STATUS_CACHE_TTL_SECONDS = 5
MAX_BACKOFF_MULTIPLIER = 8


class CaphaPushDispatcher:
    """Hintergrund-Thread für CaptchaSolverr-Push-Anfragen.
    
    Nutzt die neue CaptchaSolverr v1 API für asynchrone Captcha-Lösung.
    """

    def __init__(self, state_module=shared_state, interval_seconds: Optional[int] = None) -> None:
        self.shared_state = state_module
        configured_interval = interval_seconds or int(
            self.shared_state.values.get("captchasolverr_retry_backoff") or
            self.shared_state.values.get("capha_retry_backoff", DEFAULT_PUSH_INTERVAL_SECONDS)
        )
        self.interval_seconds = max(1, configured_interval)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._failure_streak = 0
        self._backoff_until = 0.0
        self._status_cache: Optional[ServiceStatus] = None
        self._status_cache_ts = 0.0
        self._client: Optional[CaptchaSolverrClient] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="capha-push-dispatcher",
            daemon=True,
        )
        self._thread.start()
        info(f"CaptchaSolverr Push-Dispatcher gestartet (Intervall: {self.interval_seconds}s)")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._run_once()
            except Exception as exc:  # pragma: no cover - reine Sicherung
                info(f"CaptchaSolverr Push-Dispatcher Fehler: {exc}")
            finally:
                self._stop_event.wait(self.interval_seconds)

    def _run_once(self) -> None:
        # Prüfe ob Parallel-Mode aktiviert ist (neue oder alte Config-Keys)
        parallel_enabled = (
            self.shared_state.values.get("captchasolverr_parallel_mode") or
            self.shared_state.values.get("capha_parallel_mode")
        )
        if not parallel_enabled:
            return

        now = time.time()
        if self._backoff_until and now < self._backoff_until:
            debug(f"CaptchaSolverr Push-Dispatcher pausiert für {self._backoff_until - now:.1f}s")
            return

        # Client erstellen oder cached Client verwenden
        if not self._client:
            self._client = create_captchasolverr_client(self.shared_state)
        
        if not self._client:
            debug("CaptchaSolverr Push-Dispatcher übersprungen – kein Client verfügbar")
            return

        callback_url = self._build_callback_url()
        if not callback_url:
            debug("CaptchaSolverr Push-Dispatcher übersprungen – keine callback_url ermittelbar")
            return

        push_jobs.cleanup_expired_jobs()
        current_jobs = push_jobs.list_jobs()
        max_slots = int(
            self.shared_state.values.get("captchasolverr_parallel_max") or
            self.shared_state.values.get("capha_parallel_max", 1)
        )
        
        # Zähle aktive Jobs lokal
        active_jobs = sum(1 for job in current_jobs.values() if job.get("status") in ACTIVE_PUSH_STATUSES)
        
        # Prüfe zuerst, ob es überhaupt Kandidaten gibt
        assigned_packages = {
            (job.get("payload") or {}).get("package_id") or job_id
            for job_id, job in current_jobs.items()
        }
        
        # Hole Kandidaten ohne Limit zunächst, um zu prüfen ob welche existieren
        candidates_list = list(self._select_candidates(assigned_packages, limit=max_slots))
        
        if not candidates_list:
            # Keine Kandidaten vorhanden – keine Status-Abfrage nötig
            return
        
        # Nur wenn Kandidaten vorhanden: Status vom Server abrufen
        remote_capacity = self._fetch_remote_capacity(max_slots)
        allowed_slots = min(max_slots, remote_capacity) if remote_capacity is not None else max_slots
        available_slots = max(0, allowed_slots - active_jobs)
        
        self.shared_state.update(
            "capha_push_runtime",
            {
                "max_slots": max_slots,
                "remote_capacity": remote_capacity,
                "allowed_slots": allowed_slots,
                "active_jobs": active_jobs,
                "available_slots": available_slots,
                "last_run": now,
            },
        )
        
        if available_slots <= 0:
            return

        # Begrenze Kandidaten auf verfügbare Slots
        candidates = candidates_list[:available_slots]
        dispatched = 0
        for package_id, data, prioritized_links in candidates:
            dispatched += 1
            existing_job = push_jobs.get_job(package_id)
            attempt = int(existing_job.get("attempt", 0) + 1) if existing_job else 1
            solve_payload = self._build_solve_payload(
                package_id,
                data,
                prioritized_links,
                callback_url,
            )

            push_jobs.upsert_job(
                package_id,
                {
                    "status": "pending",
                    "attempt": attempt,
                    "payload": solve_payload,
                },
            )

            try:
                # Nutze die neue v1 API
                result = self._client.solve_async(
                    captcha_type="sponsors_helper",
                    payload=solve_payload.get("payload", {}),
                    callback_url=callback_url,
                    job_id=package_id,
                    timeout_seconds=solve_payload.get("timeout_seconds", 300),
                )
            except CaptchaSolverrError as exc:
                push_jobs.remove_job(package_id)
                info(f"CaptchaSolverr Push fehlgeschlagen (job={package_id}): {exc}")
                self._record_failure()
                continue

            push_jobs.update_job_status(
                package_id,
                "sent",
                remote_job_id=result.job_id,
                handler_id=None,
                last_sent=time.time(),
            )
            info(f"CaptchaSolverr Push erfolgreich (job={package_id}, status={result.status.value}, links={len(prioritized_links)})")

        if dispatched:
            debug(f"CaptchaSolverr Push-Dispatcher hat {dispatched} Jobs initiiert")
            self._failure_streak = 0
            self._backoff_until = 0.0
            self.shared_state.update("captchasolverr_push_failure_streak", 0)
            self.shared_state.update("captchasolverr_push_backoff_until", 0.0)

    def _select_candidates(
        self,
        assigned_packages: Iterable[str],
        limit: int,
    ) -> Iterable[Tuple[str, Dict[str, Any], list]]:
        protected_entries = self.shared_state.get_db("protected").retrieve_all_titles() or []
        assigned = set(filter(None, assigned_packages))
        picked = 0
        for package_id, raw_data in protected_entries:
            if package_id in assigned:
                continue
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                continue
            if data.get("session"):
                continue
            prioritized_links = self._prioritize_links(data.get("links", []))
            if not prioritized_links:
                continue
            yield package_id, data, prioritized_links
            picked += 1
            if picked >= limit:
                break

    @staticmethod
    def _prioritize_links(links: Any) -> list:
        if not isinstance(links, list):
            return []
        rapid = [ln for ln in links if isinstance(ln, list) and len(ln) > 1 and "rapidgator" in ln[1].lower()]
        others = [ln for ln in links if isinstance(ln, list) and len(ln) > 1 and "rapidgator" not in ln[1].lower()]
        return rapid + others

    def _build_solve_payload(
        self,
        package_id: str,
        data: Dict[str, Any],
        links: list,
        callback_url: str,
    ) -> Dict[str, Any]:
        ttl_seconds = push_jobs.PUSH_JOB_TTL_SECONDS
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat() + "Z"
        mirror_val = data.get("mirror")
        mirror = None if mirror_val == "None" else mirror_val
        payload = {
            "mode": "async",
            "job_id": package_id,
            "captcha_type": "sponsors_helper",
            "callback_url": callback_url,
            "timeout_seconds": ttl_seconds,
            "payload": {
                "package_id": package_id,
                "name": data.get("title"),
                "links": links,
                "mirror": mirror,
                "password": data.get("password", ""),
                "max_attempts": int(data.get("max_attempts", 3)),
                "expires_at": expires_at,
            },
        }
        return payload

    def _build_callback_url(self) -> Optional[str]:
        external = self.shared_state.values.get("external_address") or self.shared_state.values.get("internal_address")
        if not external:
            return None
        url = external.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
        return url.rstrip("/") + "/sponsors_helper/api/captcha_callback/"

    def _fetch_remote_capacity(self, fallback: int) -> int:
        """Holt die verfügbare Kapazität vom CaptchaSolverr-Service.
        
        Nutzt die neue v1 API /v1/status.
        """
        now = time.time()
        
        # Cache prüfen
        if self._status_cache and now - self._status_cache_ts < STATUS_CACHE_TTL_SECONDS:
            if self._status_cache.has_capacity:
                return max(0, self._status_cache.available_slots)

        if not self._client:
            return fallback

        try:
            status = self._client.get_status()
        except CaptchaSolverrError as exc:
            debug(f"CaptchaSolverr Status konnte nicht geladen werden: {exc}")
            return fallback

        self._status_cache = status
        self._status_cache_ts = now
        
        # Status im shared_state speichern für Monitoring
        try:
            shared_state.update("captchasolverr_status", {
                "status": status.status,
                "version": status.version,
                "active_jobs": status.active_jobs,
                "max_concurrent": status.max_concurrent,
                "available_slots": status.available_slots,
                "queue_length": status.queue_length,
            })
            shared_state.update("captchasolverr_status_ts", now)
        except Exception:
            pass
        
        return max(0, status.available_slots)

    def _record_failure(self) -> None:
        """Zeichnet einen Fehler auf und aktiviert Backoff."""
        base = max(1, int(
            self.shared_state.values.get("captchasolverr_retry_backoff") or
            self.shared_state.values.get("capha_retry_backoff", DEFAULT_PUSH_INTERVAL_SECONDS)
        ))
        self._failure_streak += 1
        multiplier = min(MAX_BACKOFF_MULTIPLIER, 2 ** (self._failure_streak - 1))
        backoff = base * multiplier
        self._backoff_until = time.time() + backoff
        debug(f"CaptchaSolverr Push-Dispatcher Backoff aktiv ({backoff}s, streak={self._failure_streak})")
        self.shared_state.update("captchasolverr_push_failure_streak", self._failure_streak)
        self.shared_state.update("captchasolverr_push_backoff_until", self._backoff_until)


__all__ = ["CaphaPushDispatcher"]
