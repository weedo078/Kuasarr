# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

import json

from bottle import request, abort, response

from kuasarr.downloads import fail
from kuasarr.providers import shared_state, push_jobs
from kuasarr.providers.log import info, debug
from kuasarr.providers.notifications import send_discord_message
from kuasarr.providers.statistics import StatsHelper


def setup_sponsors_helper_routes(app):
    @app.get("/sponsors_helper/api/to_decrypt/")
    def to_decrypt_api():
        try:
            if not shared_state.values["helper_active"]:
                shared_state.update("helper_active", True)
                info(f"CaptchaHelper successfully connected")

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
                downloaded = shared_state.download_package(download_links, title, password, package_id)
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

            blob = json.dumps(
                {
                    "title": name,
                    "links": [replace_url, mirror],
                    "size_mb": 0,
                    "password": password,
                    "mirror": mirror,
                    "session": session
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
            if payload["activate"]:
                shared_state.update("helper_active", True)
                info(f"Sponsor status activated successfully")
                return "Sponsor status activated successfully!"
        except:
            pass
        return abort(500, "Failed")

    @app.post("/sponsors_helper/api/captcha_callback/")
    def captcha_callback_api():
        """
        Callback-Endpoint für CapHa Parallel-Mode.
        CapHa sendet Ergebnisse hierher nach erfolgreicher/fehlgeschlagener Entschlüsselung.
        
        Erwartetes Payload-Format (gemäß how-to-talk.md):
        {
            "status": "finished" | "failed",
            "job_id": "kuasarr_1234",
            "result": {
                "job_id": "kuasarr_1234",
                "urls": ["https://rapidgator.net/..."],
                "replace_url": null,
                "mirror": "Rapidgator",
                "session": null
            },
            "error": "..." (nur bei status=failed)
        }
        """
        try:
            data = request.json
            if not data:
                debug("Callback: Leerer Request-Body")
                return abort(400, "Empty request body")

            job_id = data.get("job_id")
            status = data.get("status")
            result = data.get("result") or {}
            error_msg = data.get("error")

            if not job_id:
                debug("Callback: Fehlende job_id")
                return abort(400, "Missing job_id")

            debug(f"Callback empfangen: job_id={job_id} status={status}")

            # Prüfe ob Job bekannt ist
            existing_job = push_jobs.get_job(job_id)
            if not existing_job:
                # Job nicht gefunden - möglicherweise bereits verarbeitet oder abgelaufen
                debug(f"Callback: Job {job_id} nicht gefunden (bereits verarbeitet?)")
                response.status = 200
                return {"status": "ignored", "reason": "job_not_found"}

            # Idempotenz: Prüfe ob bereits verarbeitet
            # ABER: finished überschreibt failed (Retry war erfolgreich)
            if existing_job.get("status") in ("done", "failed"):
                if status == "finished" and existing_job.get("status") == "failed":
                    # Retry war erfolgreich - weiter verarbeiten
                    debug(f"Callback: Job {job_id} war failed, aber Retry erfolgreich - verarbeite finished")
                else:
                    debug(f"Callback: Job {job_id} bereits verarbeitet (status={existing_job.get('status')})")
                    response.status = 200
                    return {"status": "already_processed"}

            if status == "finished":
                # Erfolgreiche Entschlüsselung
                urls = result.get("urls") or []
                replace_url = result.get("replace_url")
                mirror = result.get("mirror")
                session = result.get("session")
                
                # Hole Original-Paketdaten
                package_data = None
                try:
                    raw_data = shared_state.get_db("protected").retrieve(job_id)
                    if raw_data:
                        package_data = json.loads(raw_data)
                except Exception as e:
                    debug(f"Callback: Fehler beim Laden der Paketdaten für {job_id}: {e}")

                title = result.get("name") or (package_data.get("title") if package_data else job_id)
                password = result.get("password") or (package_data.get("password", "") if package_data else "")

                if replace_url and mirror and session:
                    # Weiterer Captcha-Schritt erforderlich (z.B. Rapidgator nach Filecrypt)
                    blob = json.dumps({
                        "title": title,
                        "links": [[replace_url, mirror]],
                        "size_mb": package_data.get("size_mb", 0) if package_data else 0,
                        "password": password,
                        "mirror": mirror,
                        "session": session
                    })
                    shared_state.get_db("protected").update_store(job_id, blob)
                    push_jobs.update_job_status(job_id, "pending")  # Zurück in Queue für nächsten Schritt
                    info(f"Callback: Weiterer Captcha-Schritt für {title} ({mirror})")
                    StatsHelper(shared_state).increment_captcha_decryptions_automatic()
                    return {"status": "replacement_stored", "job_id": job_id}

                elif urls:
                    # Finale Download-URLs erhalten
                    info(f"Callback: {len(urls)} Download-Links für {title} empfangen")
                    downloaded = shared_state.download_package(urls, title, password, job_id)
                    
                    if downloaded:
                        StatsHelper(shared_state).increment_package_with_links(urls)
                        StatsHelper(shared_state).increment_captcha_decryptions_automatic()
                        shared_state.get_db("protected").delete(job_id)
                        push_jobs.remove_job(job_id)
                        send_discord_message(shared_state, title=title, case="solved")
                        info(f"Callback: Download erfolgreich gestartet für {title}")
                        return {"status": "downloaded", "job_id": job_id, "links": len(urls)}
                    else:
                        # Download fehlgeschlagen
                        push_jobs.update_job_status(job_id, "failed", error="download_failed")
                        StatsHelper(shared_state).increment_failed_decryptions_automatic()
                        info(f"Callback: Download fehlgeschlagen für {title}")
                        return abort(500, "Download failed")
                else:
                    # Keine URLs und kein Replacement - unerwarteter Zustand
                    debug(f"Callback: Keine URLs und kein Replacement für {job_id}")
                    push_jobs.update_job_status(job_id, "failed", error="no_urls")
                    return abort(400, "No URLs or replacement in result")

            elif status == "failed":
                # Entschlüsselung fehlgeschlagen
                push_jobs.update_job_status(job_id, "failed", error=error_msg)
                
                # Prüfe Retry-Logik
                attempt = existing_job.get("attempt", 1)
                max_attempts = (existing_job.get("payload") or {}).get("max_attempts", 3)
                
                if attempt < max_attempts:
                    # Zurück in Queue für Retry
                    push_jobs.update_job_status(job_id, "pending", attempt=attempt + 1)
                    info(f"Callback: Job {job_id} fehlgeschlagen (Versuch {attempt}/{max_attempts}), Retry geplant")
                    return {"status": "retry_scheduled", "job_id": job_id, "attempt": attempt + 1}
                else:
                    # Max Retries erreicht - als fehlgeschlagen markieren
                    try:
                        raw_data = shared_state.get_db("protected").retrieve(job_id)
                        if raw_data:
                            package_data = json.loads(raw_data)
                            title = package_data.get("title", job_id)
                            failed = fail(title, job_id, shared_state, reason=f"CapHa: {error_msg or 'Max attempts reached'}")
                            if failed:
                                shared_state.get_db("protected").delete(job_id)
                                send_discord_message(shared_state, title=title, case="failed")
                    except Exception as e:
                        debug(f"Callback: Fehler beim Markieren als fehlgeschlagen: {e}")
                    
                    push_jobs.remove_job(job_id)
                    StatsHelper(shared_state).increment_failed_decryptions_automatic()
                    info(f"Callback: Job {job_id} endgültig fehlgeschlagen nach {attempt} Versuchen")
                    return {"status": "failed", "job_id": job_id, "error": error_msg}

            else:
                debug(f"Callback: Unbekannter Status '{status}' für Job {job_id}")
                return abort(400, f"Unknown status: {status}")

        except Exception as e:
            info(f"Callback: Fehler bei Verarbeitung: {e}")
            return abort(500, str(e))

    @app.get("/sponsors_helper/api/status/")
    def get_status():
        """Status-Endpoint für CapHa und Monitoring."""
        try:
            parallel_mode = shared_state.values.get("capha_parallel_mode", False)
            push_runtime = shared_state.values.get("capha_push_runtime", {})
            capha_status = shared_state.values.get("capha_status", {})
            
            # Zähle protected packages
            protected = shared_state.get_db("protected").retrieve_all_titles() or []
            protected_count = len(protected)
            
            # Push-Job-Statistiken
            jobs = push_jobs.list_jobs()
            job_stats = {
                "total": len(jobs),
                "pending": sum(1 for j in jobs.values() if j.get("status") == "pending"),
                "sent": sum(1 for j in jobs.values() if j.get("status") == "sent"),
                "failed": sum(1 for j in jobs.values() if j.get("status") == "failed"),
            }
            
            return {
                "helper_active": shared_state.values.get("helper_active", False),
                "parallel_mode_active": parallel_mode,
                "protected_packages": protected_count,
                "capha_detected": bool(capha_status),
                "capha_status": capha_status if capha_status else None,
                "push_runtime": push_runtime if parallel_mode else None,
                "push_jobs": job_stats if parallel_mode else None,
            }
        except Exception as e:
            return {"error": str(e)}
