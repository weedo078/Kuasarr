# -*- coding: utf-8 -*-
"""CaptchaSolverr v1 API Client für Kuasarr.

Dieser Client kommuniziert mit der neuen generischen CaptchaSolverr API (/v1/).
Er ersetzt die alte CapHa-spezifische Kommunikation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from requests import RequestException

from kuasarr.providers.log import info, debug, error


class CaptchaSolverrError(RuntimeError):
    """Basis-Exception für CaptchaSolverr-Fehler."""


class JobStatus(str, Enum):
    """Status eines CaptchaSolverr-Jobs."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    FINISHED = "finished"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class SolveResult:
    """Ergebnis eines Solve-Aufrufs."""
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @property
    def is_complete(self) -> bool:
        return self.status in (JobStatus.FINISHED, JobStatus.FAILED, JobStatus.TIMEOUT)
    
    @property
    def is_success(self) -> bool:
        return self.status == JobStatus.FINISHED


@dataclass
class ServiceStatus:
    """Status des CaptchaSolverr-Service."""
    status: str
    version: str
    active_jobs: int
    max_concurrent: int
    available_slots: int
    queue_length: int
    supported_types: List[str]
    
    @property
    def is_ready(self) -> bool:
        return self.status == "ready"
    
    @property
    def has_capacity(self) -> bool:
        return self.available_slots > 0


def _normalize_base_url(raw_url: str) -> str:
    """Normalisiert die Base-URL."""
    if not raw_url:
        raise ValueError("CaptchaSolverr-URL ist nicht konfiguriert")
    url = raw_url.strip()
    if not url:
        raise ValueError("CaptchaSolverr-URL ist leer")
    return url.rstrip('/')


class CaptchaSolverrClient:
    """HTTP-Client für die CaptchaSolverr v1 API.
    
    Unterstützt sowohl synchrone als auch asynchrone Captcha-Lösung.
    
    Beispiel:
        client = CaptchaSolverrClient("http://captchasolverr:9700")
        
        # Async-Modus (empfohlen für Batch-Verarbeitung)
        result = client.solve_async(
            captcha_type="sponsors_helper",
            payload={"url": "https://...", "links": [...]},
            callback_url="http://kuasarr:8080/api/captcha_callback/job123"
        )
        
        # Später: Ergebnis abrufen
        result = client.get_result(result.job_id)
        
        # Sync-Modus (blockiert bis Ergebnis)
        result = client.solve_sync(
            captcha_type="sponsors_helper",
            payload={"url": "https://..."}
        )
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retries: int = 3,
        backoff_seconds: int = 5,
        api_version: str = "v1",
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.timeout = max(1, int(timeout))
        self.retries = max(1, int(retries))
        self.backoff_seconds = max(1, int(backoff_seconds))
        self.api_version = api_version
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Kuasarr-CaptchaSolverrClient/1.0"
        })

    def _build_url(self, path: str) -> str:
        """Baut die vollständige URL mit API-Version."""
        if path.startswith('/'):
            path = path[1:]
        return f"{self.base_url}/{self.api_version}/{path}"

    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Führt einen HTTP-Request mit Retry-Logik aus."""
        url = self._build_url(path)
        last_exc: Optional[Exception] = None
        
        for attempt in range(1, self.retries + 1):
            try:
                debug(f"CaptchaSolverr {method.upper()} {url} (Versuch {attempt}/{self.retries})")
                
                response = self._session.request(
                    method.upper(),
                    url,
                    json=json_data,
                    headers=headers,
                    timeout=self.timeout,
                )
                
                # Capacity-Header auslesen falls vorhanden
                capacity_header = response.headers.get("X-CaptchaSolverr-Capacity")
                if capacity_header:
                    debug(f"CaptchaSolverr Capacity: {capacity_header}")
                
                response.raise_for_status()
                
                if response.headers.get("Content-Type", "").startswith("application/json"):
                    return response.json()
                return {"status_code": response.status_code, "text": response.text}
                
            except RequestException as exc:
                last_exc = exc
                info(f"CaptchaSolverr {method.upper()} {url} fehlgeschlagen ({attempt}/{self.retries}): {exc}")
                
                if attempt < self.retries:
                    sleep_for = min(self.backoff_seconds * attempt, self.backoff_seconds * self.retries)
                    time.sleep(sleep_for)
        
        raise CaptchaSolverrError(f"CaptchaSolverr {method.upper()} {url} fehlgeschlagen nach {self.retries} Versuchen") from last_exc

    # ==================== API-Methoden ====================

    def get_status(self) -> ServiceStatus:
        """Ruft den Service-Status ab.
        
        Returns:
            ServiceStatus mit Kapazitätsinformationen
        """
        data = self._request("GET", "status")
        return ServiceStatus(
            status=data.get("status", "unknown"),
            version=data.get("version", "unknown"),
            active_jobs=int(data.get("active_jobs", 0)),
            max_concurrent=int(data.get("max_concurrent", 1)),
            available_slots=int(data.get("available_slots", 0)),
            queue_length=int(data.get("queue_length", 0)),
            supported_types=data.get("supported_types", []),
        )

    def solve_async(
        self,
        captcha_type: str,
        payload: Dict[str, Any],
        callback_url: Optional[str] = None,
        job_id: Optional[str] = None,
        timeout_seconds: int = 300,
    ) -> SolveResult:
        """Sendet einen asynchronen Solve-Request.
        
        Args:
            captcha_type: Typ des Captchas (z.B. "sponsors_helper", "hcaptcha")
            payload: Captcha-spezifische Daten
            callback_url: URL für Callback bei Fertigstellung
            job_id: Optionale Job-ID (wird sonst generiert)
            timeout_seconds: Timeout für den Job
            
        Returns:
            SolveResult mit job_id und initialem Status
        """
        request_data = {
            "mode": "async",
            "captcha_type": captcha_type,
            "payload": payload,
            "timeout_seconds": timeout_seconds,
        }
        
        if callback_url:
            request_data["callback_url"] = callback_url
        if job_id:
            request_data["job_id"] = job_id
        
        data = self._request("POST", "solve", json_data=request_data)
        
        return SolveResult(
            job_id=data.get("job_id", ""),
            status=JobStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
        )

    def solve_sync(
        self,
        captcha_type: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 120,
    ) -> SolveResult:
        """Sendet einen synchronen Solve-Request (blockiert bis Ergebnis).
        
        Args:
            captcha_type: Typ des Captchas
            payload: Captcha-spezifische Daten
            timeout_seconds: Timeout für den Request
            
        Returns:
            SolveResult mit Ergebnis oder Fehler
        """
        request_data = {
            "mode": "sync",
            "captcha_type": captcha_type,
            "payload": payload,
            "timeout_seconds": timeout_seconds,
        }
        
        # Längerer Timeout für sync-Requests
        old_timeout = self.timeout
        self.timeout = max(self.timeout, timeout_seconds + 10)
        
        try:
            data = self._request("POST", "solve", json_data=request_data)
        finally:
            self.timeout = old_timeout
        
        return SolveResult(
            job_id=data.get("job_id", ""),
            status=JobStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
        )

    def get_result(self, job_id: str) -> SolveResult:
        """Ruft das Ergebnis eines Jobs ab.
        
        Args:
            job_id: Die Job-ID
            
        Returns:
            SolveResult mit aktuellem Status und ggf. Ergebnis
        """
        data = self._request("GET", f"result/{job_id}")
        
        return SolveResult(
            job_id=data.get("job_id", job_id),
            status=JobStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
        )

    def poll_result(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> SolveResult:
        """Pollt das Ergebnis eines Jobs bis zur Fertigstellung.
        
        Args:
            job_id: Die Job-ID
            poll_interval: Sekunden zwischen Polls
            max_wait: Maximale Wartezeit in Sekunden
            
        Returns:
            SolveResult mit finalem Status
        """
        start = time.time()
        
        while time.time() - start < max_wait:
            result = self.get_result(job_id)
            
            if result.is_complete:
                return result
            
            debug(f"Job {job_id} noch nicht fertig (Status: {result.status}), warte {poll_interval}s...")
            time.sleep(poll_interval)
        
        return SolveResult(
            job_id=job_id,
            status=JobStatus.TIMEOUT,
            error=f"Timeout nach {max_wait}s",
        )

    def send_callback(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_msg: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sendet einen Callback an CaptchaSolverr (für bidirektionale Kommunikation).
        
        Args:
            job_id: Die Job-ID
            status: "finished" oder "failed"
            result: Ergebnis-Daten bei Erfolg
            error_msg: Fehlermeldung bei Fehler
            
        Returns:
            Response-Daten
        """
        callback_data: Dict[str, Any] = {"status": status}
        
        if result:
            callback_data["result"] = result
        if error_msg:
            callback_data["error"] = error_msg
        
        return self._request("POST", f"callback/{job_id}", json_data=callback_data)


def create_captchasolverr_client(shared_state) -> Optional[CaptchaSolverrClient]:
    """Factory-Funktion: Erstellt einen CaptchaSolverrClient aus shared_state.
    
    Prüft zuerst die neuen Config-Keys, fällt auf Legacy-Keys zurück.
    """
    # Neue Config-Keys (v1 API)
    base_url = (
        shared_state.values.get("captchasolverr_url") or
        shared_state.values.get("capha_url") or  # Legacy-Fallback
        ""
    ).strip()
    
    if not base_url:
        return None
    
    timeout = int(shared_state.values.get("captchasolverr_timeout") or 
                  shared_state.values.get("capha_timeout", 30))
    retries = int(shared_state.values.get("captchasolverr_retries") or
                  shared_state.values.get("capha_retries", 3))
    backoff = int(shared_state.values.get("captchasolverr_retry_backoff") or
                  shared_state.values.get("capha_retry_backoff", 5))
    
    return CaptchaSolverrClient(
        base_url,
        timeout=timeout,
        retries=retries,
        backoff_seconds=backoff,
    )


# Legacy-Alias für Abwärtskompatibilität
CaphaClient = CaptchaSolverrClient
CaphaClientError = CaptchaSolverrError
create_capha_client_from_state = create_captchasolverr_client


__all__ = [
    "CaptchaSolverrClient",
    "CaptchaSolverrError",
    "SolveResult",
    "ServiceStatus",
    "JobStatus",
    "create_captchasolverr_client",
    # Legacy-Aliase
    "CaphaClient",
    "CaphaClientError",
    "create_capha_client_from_state",
]
