# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from bottle import request, abort, response

from kuasarr.downloads import fail
from kuasarr.providers import shared_state
from kuasarr.providers.log import info
from kuasarr.providers.notifications import send_discord_message
from kuasarr.providers.statistics import StatsHelper
from kuasarr.storage.config import Config


PARALLEL_HANDLER_TTL_SECONDS = 300
PARALLEL_JOB_TTL_SECONDS = 180
PARALLEL_POLL_AFTER_SECONDS = 15
PARALLEL_COMPLETED_TTL_SECONDS = 600
PARALLEL_MIN_POLL_INTERVAL = 5


def _require_parallel_api_key() -> None:
    api_key = Config('API').get('key')
    if not api_key:
        return

    provided_key = (
        request.headers.get("X-API-Key")
        or request.query.get("apikey")
        or request.query.get("api_key")
    )

    if not provided_key:
        abort(401, "API-Schlüssel benötigt")
    if provided_key != api_key:
        abort(403, "API-Schlüssel ungültig")


def _load_dict(key: str) -> Dict[str, Any]:
    value = shared_state.values.get(key)
    if isinstance(value, dict):
        return dict(value)
    return {}


def _save_dict(key: str, value: Dict[str, Any]) -> None:
    shared_state.update(key, value)


def _cleanup_handlers(handlers: Dict[str, Any]) -> bool:
    now_ts = time.time()
    changed = False
    for handler_id, info in list(handlers.items()):
        last_seen = float(info.get("last_seen", 0.0))
        if now_ts - last_seen > PARALLEL_HANDLER_TTL_SECONDS:
            handlers.pop(handler_id, None)
            changed = True
    return changed


def _cleanup_jobs(jobs: Dict[str, Any]) -> bool:
    now_ts = time.time()
    changed = False
    for job_id, info in list(jobs.items()):
        expires_at = float(info.get("expires_at", 0.0))
        if expires_at and now_ts > expires_at:
            jobs.pop(job_id, None)
            changed = True
    return changed


def _is_parallel_enabled() -> bool:
    return bool(shared_state.values.get("capha_parallel_mode"))


def _cleanup_completed_jobs(completed_jobs: Dict[str, Any]) -> bool:
    now_ts = time.time()
    changed = False
    for job_id, info in list(completed_jobs.items()):
        completed_at = float(info.get("completed_at", 0.0))
        if completed_at and now_ts - completed_at > PARALLEL_COMPLETED_TTL_SECONDS:
            completed_jobs.pop(job_id, None)
            changed = True
    return changed


def setup_sponsors_helper_routes(app):
    @app.get("/sponsors_helper/api/to_decrypt_parallel/")
    def to_decrypt_parallel_api():
        _require_parallel_api_key()
        if not _is_parallel_enabled():
            return abort(404, "Parallelmodus ist deaktiviert")

        handler_id = request.headers.get("X-Capha-Handler")
        if not handler_id:
            return abort(400, "Header 'X-Capha-Handler' fehlt")

        handlers = _load_dict("parallel_handlers")
        jobs = _load_dict("parallel_jobs")

        handlers_dirty = _cleanup_handlers(handlers)
        jobs_dirty = _cleanup_jobs(jobs)

        handler_info = handlers.get(handler_id)
        if handler_info is None:
            response.status = 409
            return {
                "jobs": [],
                "poll_after": PARALLEL_POLL_AFTER_SECONDS,
                "error": "Unbekannter Handler"
            }

        now_ts = time.time()
        handler_info["last_seen"] = now_ts
        last_poll = float(handler_info.get("last_poll", 0.0))
        if last_poll and now_ts - last_poll < PARALLEL_MIN_POLL_INTERVAL:
            wait_seconds = max(1, int(PARALLEL_MIN_POLL_INTERVAL - (now_ts - last_poll)))
            response.status = 429
            return {
                "jobs": [],
                "poll_after": wait_seconds,
                "error": "Polling zu häufig"
            }
        handler_info["last_poll"] = now_ts
        handler_slots = int(handler_info.get("slot_count", shared_state.values.get("capha_parallel_max", 1)))
        global_slots = int(shared_state.values.get("capha_parallel_max", 1))

        capacity_header = request.headers.get("X-Capha-Capacity")
        try:
            requested_capacity = int(capacity_header) if capacity_header else 1
        except ValueError:
            requested_capacity = 1
        requested_capacity = max(1, requested_capacity)

        allowed_capacity = max(1, min(requested_capacity, handler_slots, global_slots))

        protected = shared_state.get_db("protected").retrieve_all_titles()
        available_jobs: List[Dict[str, Any]] = []

        if protected:
            assigned_packages = {info.get("package_id") for info in jobs.values()}
            now_ts = time.time()

            for package_id, raw_data in protected:
                if package_id in assigned_packages:
                    continue

                data = json.loads(raw_data)

                if data.get("session"):
                    continue

                mirror = None if (mirror_val := data.get("mirror")) == "None" else mirror_val
                links: List[List[str]] = data.get("links", [])
                rapid = [ln for ln in links if len(ln) > 1 and "rapidgator" in ln[1].lower()]
                others = [ln for ln in links if len(ln) > 1 and "rapidgator" not in ln[1].lower()]
                prioritized_links = rapid + others

                if not prioritized_links:
                    continue

                expiry_ts = now_ts + PARALLEL_JOB_TTL_SECONDS
                attempt = 1

                jobs[package_id] = {
                    "package_id": package_id,
                    "handler_id": handler_id,
                    "expires_at": expiry_ts,
                    "attempt": attempt,
                    "created_at": now_ts
                }
                jobs_dirty = True

                job_payload = {
                    "job_id": package_id,
                    "name": data.get("title"),
                    "package_id": package_id,
                    "links": prioritized_links,
                    "mirror": mirror,
                    "password": data.get("password", ""),
                    "priority": 100 if rapid else 50,
                    "max_attempts": int(data.get("max_attempts", 3)),
                    "attempt": attempt,
                    "expires_at": (datetime.utcnow() + timedelta(seconds=PARALLEL_JOB_TTL_SECONDS)).isoformat() + "Z"
                }

                available_jobs.append(job_payload)

                if len(available_jobs) >= allowed_capacity:
                    break

        handler_active_jobs = len([job for job in jobs.values() if job.get("handler_id") == handler_id])
        handler_info["active_jobs"] = handler_active_jobs
        handlers[handler_id] = handler_info
        handlers_dirty = True

        if handlers_dirty:
            _save_dict("parallel_handlers", handlers)
        if jobs_dirty:
            _save_dict("parallel_jobs", jobs)

        if not available_jobs:
            response.status = 404
            return {
                "jobs": [],
                "poll_after": PARALLEL_POLL_AFTER_SECONDS
            }

        response.status = 200
        return {
            "jobs": available_jobs,
            "poll_after": PARALLEL_POLL_AFTER_SECONDS
        }

    @app.post("/sponsors_helper/api/register_handler/")
    def register_handler_api():
        _require_parallel_api_key()
        if not _is_parallel_enabled():
            return abort(404, "Parallelmodus ist deaktiviert")

        payload = request.json
        if not isinstance(payload, dict):
            return abort(400, "Ungültiger Payload")

        handler_id = payload.get("id") or payload.get("handler_id")
        if not handler_id:
            return abort(400, "'id' fehlt im Payload")

        if not payload.get("parallel", False):
            return abort(400, "Parallelkennzeichnung fehlt oder ist false")

        slot_count = payload.get("slot_count") or payload.get("slots")
        try:
            slot_count = int(slot_count) if slot_count is not None else int(shared_state.values.get("capha_parallel_max", 1))
        except (TypeError, ValueError):
            slot_count = int(shared_state.values.get("capha_parallel_max", 1))
        slot_count = max(1, slot_count)

        handler_name = payload.get("handler", "Unnamed")
        version = payload.get("version")
        now_ts = time.time()

        handlers = _load_dict("parallel_handlers")
        jobs = _load_dict("parallel_jobs")

        handlers[handler_id] = {
            "name": handler_name,
            "version": version,
            "slot_count": slot_count,
            "registered_at": now_ts,
            "last_seen": now_ts,
            "active_jobs": len([job for job in jobs.values() if job.get("handler_id") == handler_id])
        }

        _save_dict("parallel_handlers", handlers)

        response.status = 201
        return {
            "status": "registered",
            "handler_id": handler_id,
            "slot_count": slot_count,
            "poll_after": PARALLEL_POLL_AFTER_SECONDS
        }

    @app.delete("/sponsors_helper/api/register_handler/<handler_id>")
    def unregister_handler_api(handler_id):
        _require_parallel_api_key()
        handlers = _load_dict("parallel_handlers")
        jobs = _load_dict("parallel_jobs")

        removed = handlers.pop(handler_id, None)
        if removed is None:
            return abort(404, "Handler nicht gefunden")

        jobs_changed = False
        for job_id, job_info in list(jobs.items()):
            if job_info.get("handler_id") == handler_id:
                jobs.pop(job_id, None)
                jobs_changed = True

        _save_dict("parallel_handlers", handlers)
        if jobs_changed:
            _save_dict("parallel_jobs", jobs)

        return {"status": "deregistered", "handler_id": handler_id}

    @app.post("/sponsors_helper/api/to_download_parallel/")
    def to_download_parallel_api():
        _require_parallel_api_key()
        if not _is_parallel_enabled():
            return abort(404, "Parallelmodus ist deaktiviert")

        handler_id = request.headers.get("X-Capha-Handler")
        if not handler_id:
            return abort(400, "Header 'X-Capha-Handler' fehlt")

        payload = request.json
        if not isinstance(payload, dict):
            return abort(400, "Ungültiger Payload")

        job_id = payload.get("job_id") or payload.get("package_id")
        if not job_id:
            return abort(400, "'job_id' fehlt im Payload")

        download_links = payload.get("urls") or []
        if not isinstance(download_links, list) or not download_links:
            return abort(400, "'urls' fehlt oder ist leer")

        handlers = _load_dict("parallel_handlers")
        handler_info = handlers.get(handler_id)
        if handler_info is None:
            return abort(409, "Unbekannter Handler")

        jobs = _load_dict("parallel_jobs")
        completed_jobs = _load_dict("parallel_completed_jobs")
        completed_dirty = _cleanup_completed_jobs(completed_jobs)

        job_info = jobs.get(job_id)
        if job_info is None or job_info.get("handler_id") != handler_id:
            completed_info = completed_jobs.get(job_id)
            if completed_info and completed_info.get("handler_id") == handler_id:
                response.status = 200
                if completed_info.get("original_status") == 500:
                    status_text = "failed"
                else:
                    status_text = completed_info.get("status", "already_processed")
                return {
                    "status": status_text,
                    "job_id": job_id,
                    "message": completed_info.get(
                        "message", "Paralleljob wurde bereits verarbeitet"
                    ),
                    "original_status": completed_info.get("original_status", 202),
                }
            return abort(404, "Unbekannter Job")

        package_id = payload.get("package_id") or job_id
        title = payload.get("name")
        password = payload.get("password") or ""
        mirror = payload.get("mirror")

        destination_path = None
        stored_blob = shared_state.get_db("protected").retrieve(package_id)
        if stored_blob:
            try:
                stored_data = json.loads(stored_blob)
                destination_path = stored_data.get("destination_path")
                if not title:
                    title = stored_data.get("title")
                if not mirror:
                    mirror = stored_data.get("mirror")
                if not password:
                    password = stored_data.get("password", "")
            except json.JSONDecodeError:
                destination_path = None

        try:
            downloaded = shared_state.download_package(
                download_links,
                title,
                password,
                package_id,
                destination_folder=destination_path,
            )
        except Exception as exc:
            info(f"Error starting parallel download for {title}: {exc}")
            downloaded = False

        jobs.pop(job_id, None)
        _save_dict("parallel_jobs", jobs)

        handler_info["active_jobs"] = max(0, handler_info.get("active_jobs", 0) - 1)
        handler_info["last_seen"] = time.time()
        handlers[handler_id] = handler_info
        _save_dict("parallel_handlers", handlers)

        stats_helper = StatsHelper(shared_state)

        if downloaded:
            stats_helper.increment_package_with_links(download_links)
            stats_helper.increment_captcha_decryptions_automatic()
            stats_helper.increment_parallel_success()
            shared_state.get_db("protected").delete(package_id)
            send_discord_message(shared_state, title=title, case="solved")
            info(f"Parallel download successfully started for {title}")
            completed_jobs[job_id] = {
                "handler_id": handler_id,
                "status": "queued",
                "message": "Paralleljob wurde bereits verarbeitet",
                "original_status": 202,
                "completed_at": time.time(),
            }
            _save_dict("parallel_completed_jobs", completed_jobs)
            response.status = 202
            return {"status": "queued", "job_id": job_id}

        stats_helper.increment_failed_decryptions_automatic()
        stats_helper.increment_parallel_failure()
        fail(title or "unknown", package_id, shared_state, reason="Parallel download failed")
        completed_jobs[job_id] = {
            "handler_id": handler_id,
            "status": "failed",
            "message": "Paralleljob wurde bereits als fehlgeschlagen markiert",
            "original_status": 500,
            "completed_at": time.time(),
        }
        _save_dict("parallel_completed_jobs", completed_jobs)
        return abort(500, "Parallel download konnte nicht gestartet werden")

        if completed_dirty:
            _save_dict("parallel_completed_jobs", completed_jobs)

    @app.get("/sponsors_helper/api/status/")
    def sponsors_helper_status_api():
        handlers = _load_dict("parallel_handlers")
        jobs = _load_dict("parallel_jobs")

        handlers_dirty = _cleanup_handlers(handlers)
        jobs_dirty = _cleanup_jobs(jobs)

        if handlers_dirty:
            _save_dict("parallel_handlers", handlers)
        if jobs_dirty:
            _save_dict("parallel_jobs", jobs)

        parallel_enabled = _is_parallel_enabled()
        max_slots = int(shared_state.values.get("capha_parallel_max", 1))
        active_parallel_jobs = len(jobs)
        available_parallel_slots = max(0, max_slots - active_parallel_jobs)

        protected_entries = shared_state.get_db("protected").retrieve_all_titles() or []
        queued_packages = len(protected_entries)
        assigned_packages = {info.get("package_id") for info in jobs.values() if isinstance(info, dict)}
        unassigned_packages = len([pkg_id for pkg_id, _ in protected_entries if pkg_id not in assigned_packages])

        handler_metrics: List[Dict[str, Any]] = []
        now_ts = time.time()
        for handler_id, info_dict in handlers.items():
            slot_count = int(info_dict.get("slot_count", max_slots))
            active_jobs = int(info_dict.get("active_jobs", 0))
            last_seen = float(info_dict.get("last_seen", 0.0))
            handler_metrics.append(
                {
                    "handler_id": handler_id,
                    "name": info_dict.get("name"),
                    "version": info_dict.get("version"),
                    "slot_count": slot_count,
                    "active_jobs": active_jobs,
                    "available_slots": max(0, slot_count - active_jobs),
                    "last_seen": last_seen,
                    "seconds_since_seen": max(0, now_ts - last_seen),
                }
            )

        stats_helper = StatsHelper(shared_state)
        stats = stats_helper.get_stats()
        parallel_stats = {
            "jobs_succeeded": stats.get("parallel_jobs_succeeded", 0),
            "jobs_failed": stats.get("parallel_jobs_failed", 0),
            "success_rate": stats.get("parallel_success_rate", 0.0),
            "total_jobs": stats.get("total_parallel_jobs", 0),
        }

        response.status = 200
        return {
            "parallel_enabled": parallel_enabled,
            "max_parallel_slots": max_slots,
            "active_parallel_jobs": active_parallel_jobs,
            "available_parallel_slots": available_parallel_slots,
            "queued_packages": queued_packages,
            "queue_length": queued_packages,
            "unassigned_packages": unassigned_packages,
            "poll_after": PARALLEL_POLL_AFTER_SECONDS,
            "handler_metrics": handler_metrics,
            "parallel_stats": parallel_stats,
        }

    @app.get("/sponsors_helper/api/to_decrypt/")
    def to_decrypt_api():
        try:
            if not shared_state.values.get("helper_active"):
                return abort(403, "CaptchaHelper ist deaktiviert. Bitte manuell aktivieren.")

            protected = shared_state.get_db("protected").retrieve_all_titles()
            if not protected:
                return abort(404, "No encrypted packages found")

            # Find the first package without a "session" key
            selected_package = None
            for package in protected:
                data = json.loads(package[1])
                if "session" not in data:
                    selected_package = (package[0], data)
                    break

            if not selected_package:
                return abort(404, "No valid packages without session found")

            package_id, data = selected_package
            title = data["title"]
            links = data["links"]
            mirror = None if (mirror := data.get('mirror')) == "None" else mirror
            password = data["password"]

            rapid = [ln for ln in links if "rapidgator" in ln[1].lower()]
            others = [ln for ln in links if "rapidgator" not in ln[1].lower()]
            prioritized_links = rapid + others

            return {
                "to_decrypt": {
                    "name": title,
                    "id": package_id,
                    "url": prioritized_links,
                    "mirror": mirror,
                    "password": password,
                    "max_attempts": 3
                }
            }
        except Exception as e:
            return abort(500, str(e))

    @app.post("/sponsors_helper/api/to_download/")
    def to_download_api():
        try:
            data = request.json
            title = data.get('name')
            package_id = data.get('package_id')
            download_links = data.get('urls')
            password = data.get('password')

            info(f"Received {len(download_links)} download links for {title}")

            if download_links:
                destination_path = None
                stored_blob = shared_state.get_db("protected").retrieve(package_id)
                if stored_blob:
                    try:
                        stored_data = json.loads(stored_blob)
                        destination_path = stored_data.get("destination_path")
                    except json.JSONDecodeError:
                        destination_path = None

                downloaded = shared_state.download_package(
                    download_links,
                    title,
                    password,
                    package_id,
                    destination_folder=destination_path,
                )
                if downloaded:
                    StatsHelper(shared_state).increment_package_with_links(download_links)
                    StatsHelper(shared_state).increment_captcha_decryptions_automatic()
                    shared_state.get_db("protected").delete(package_id)
                    send_discord_message(shared_state, title=title, case="solved")
                    info(f"Download successfully started for {title}")
                    return f"Downloaded {len(download_links)} download links for {title}"
                else:
                    info(f"Download failed for {title}")

        except Exception as e:
            info(f"Error decrypting: {e}")

        StatsHelper(shared_state).increment_failed_decryptions_automatic()
        return abort(500, "Failed")  #

    @app.post("/sponsors_helper/api/to_replace/")
    def to_replace_api():
        try:
            data = request.json
            name = data.get('name')
            package_id = data.get('package_id')
            password = data.get('password')
            replace_url = data.get('replace_url')
            mirror = data.get('mirror')
            session = data.get('session')

            if not all([name, package_id, replace_url, mirror, session]):
                info("Missing required replacement data")
                return {"error": "Missing required replacement data"}, 400

            if password is None:
                password = ""

            existing_blob = shared_state.get_db("protected").retrieve(package_id)
            destination_path = None
            manual_job_id = None
            if existing_blob:
                try:
                    existing_data = json.loads(existing_blob)
                    destination_path = existing_data.get("destination_path")
                    manual_job_id = existing_data.get("manual_job_id")
                except json.JSONDecodeError:
                    destination_path = None

            blob = json.dumps(
                {
                    "title": name,
                    "links": [replace_url, mirror],
                    "size_mb": 0,
                    "password": password,
                    "mirror": mirror,
                    "session": session,
                    "destination_path": destination_path,
                    "manual_job_id": manual_job_id,
                })

            shared_state.get_db("protected").update_store(package_id, blob)

            info(f"Another CAPTCHA solution is required for {mirror} link: {replace_url}")

            StatsHelper(shared_state).increment_captcha_decryptions_automatic()

            return f"Replacement link stored for {name}"

        except Exception as e:
            StatsHelper(shared_state).increment_failed_decryptions_automatic()
            info(f"Error handling replacement: {e}")
            return {"error": str(e)}, 500

    @app.delete("/sponsors_helper/api/to_failed/")
    def move_to_failed_api():
        try:
            StatsHelper(shared_state).increment_failed_decryptions_automatic()

            data = request.json
            package_id = data.get('package_id')

            data = json.loads(shared_state.get_db("protected").retrieve(package_id))
            title = data.get('title')

            if package_id:
                info(f'Marking package "{title}" with ID "{package_id}" as failed')
                failed = fail(title, package_id, shared_state, reason="Too many failed attempts by SponsorsHelper")
                if failed:
                    shared_state.get_db("protected").delete(package_id)
                    send_discord_message(shared_state, title=title, case="failed")
                    return f'Package "{title}" with ID "{package_id} marked as failed!"'
        except Exception as e:
            info(f"Error moving to failed: {e}")

        return abort(500, "Failed")

    @app.put("/sponsors_helper/api/set_sponsor_status/")
    def activate_sponsor_status():
        try:
            data = request.body.read().decode("utf-8")
            payload = json.loads(data)
            activate = payload.get("activate")
            if activate not in {True, False}:
                return abort(400, "Ungültiger Wert für 'activate'")

            shared_state.update("helper_active", activate)
            status = "aktiviert" if activate else "deaktiviert"
            info(f"CaptchaHelper wurde {status}")
            return f"CaptchaHelper wurde {status}."
        except:
            pass
        return abort(500, "Failed")
