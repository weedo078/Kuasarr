# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

import json

from quasarr.downloads.sources.al import get_al_download_links
from quasarr.downloads.sources.dd import get_dd_download_links
from quasarr.downloads.sources.dl import get_dl_download_link, check_filecrypt_needs_captcha
from quasarr.downloads.sources.dt import get_dt_download_links
from quasarr.downloads.sources.dw import get_dw_download_links
from quasarr.downloads.sources.mb import get_mb_download_links
from quasarr.downloads.sources.nx import get_nx_download_links
from quasarr.downloads.sources.sf import get_sf_download_links, resolve_sf_redirect
from quasarr.downloads.sources.sl import get_sl_download_links
from quasarr.downloads.sources.wd import get_wd_download_links
from quasarr.providers.log import info, debug
from quasarr.providers.notifications import send_discord_message


def download(shared_state, request_from, title, url, mirror, size_mb, password, imdb_id=None):
    debug(f"[DL-DOWNLOAD-DEBUG] Download attempt:")
    debug(f"  Title: {title}")
    debug(f"  URL: {url}")
    debug(f"  Mirror: {mirror}")
    debug(f"  Size MB: {size_mb}")
    debug(f"  Password: {password}")
    debug(f"  IMDB ID: {imdb_id}")
    
    if "radarr".lower() in request_from.lower():
        category = "movies"
    else:
        category = "tv"

    package_id = f"Quasarr_{category}_{str(hash(title + url)).replace('-', '')}"
    success = True

    if imdb_id is not None and imdb_id.lower() == "none":
        imdb_id = None

    al = shared_state.values["config"]("Hostnames").get("al")
    dd = shared_state.values["config"]("Hostnames").get("dd")
    dl = shared_state.values["config"]("Hostnames").get("dl")
    dt = shared_state.values["config"]("Hostnames").get("dt")
    dw = shared_state.values["config"]("Hostnames").get("dw")
    mb = shared_state.values["config"]("Hostnames").get("mb")
    nx = shared_state.values["config"]("Hostnames").get("nx")
    sf = shared_state.values["config"]("Hostnames").get("sf")
    sl = shared_state.values["config"]("Hostnames").get("sl")
    wd = shared_state.values["config"]("Hostnames").get("wd")

    if al and al.lower() in url.lower():
        release_id = password
        payload = get_al_download_links(shared_state, url, mirror, title, release_id)
        links = payload.get("links", [])
        title = payload.get("title", title)
        password = payload.get("password", "")
        if links:
            info(f"Decrypted {len(links)} download links for {title}")
            send_discord_message(shared_state, title=title, case="unprotected", imdb_id=imdb_id, source=url)
            added = shared_state.download_package(links, title, password, package_id)
            if not added:
                fail(title, package_id, shared_state,
                     reason=f'Failed to add {len(links)} links for "{title}" to linkgrabber')
                success = False
        else:
            fail(title, package_id, shared_state,
                 reason=f'Offline / no links found for "{title}" on AL - "{url}"')
            success = False

    elif dd and dd.lower() in url.lower():
        links = get_dd_download_links(shared_state, mirror, title)
        if links:
            info(f"Decrypted {len(links)} download links for {title}")
            send_discord_message(shared_state, title=title, case="unprotected", imdb_id=imdb_id, source=url)
            added = shared_state.download_package(links, title, password, package_id)
            if not added:
                fail(title, package_id, shared_state,
                     reason=f'Failed to add {len(links)} links for "{title}" to linkgrabber', source=url)
                success = False
        else:
            fail(title, package_id, shared_state,
                 reason=f'Offline / no links found for "{title}" on DD - "{url}"')
            success = False

    elif dl and dl.lower() in url.lower():
        debug(f'[DL-DOWNLOAD] Processing DL download for "{title}" from URL: "{url}"')
        debug(f'[DL-DOWNLOAD] DL hostname configured as: "{dl}"')
        debug(f'[DL-DOWNLOAD] URL contains DL hostname: {dl.lower() in url.lower()}')
        dl_result = get_dl_download_link(shared_state, url, title)
        links = dl_result.get("links", []) if isinstance(dl_result, dict) else (dl_result if dl_result else [])
        dl_password = dl_result.get("password") if isinstance(dl_result, dict) else None
        debug(f'[DL-DOWNLOAD] Retrieved {len(links)} links with password: {"***" if dl_password else "None"}')
        if links:
            # Format links properly for protected storage
            formatted_links = []
            direct_links = []
            captcha_links = []
            
            for link in links:
                if isinstance(link, str):
                    # Detect link type and format accordingly
                    if "filecrypt" in link.lower():
                        formatted_link = [link, "filecrypt"]
                        formatted_links.append(formatted_link)
                        # Check if FileCrypt link actually needs a captcha
                        if check_filecrypt_needs_captcha(shared_state, link):
                            captcha_links.append(formatted_link)
                        else:
                            direct_links.append(link)  # CNL-ready FileCrypt goes direct to JD
                    elif "keeplinks" in link.lower():
                        formatted_link = [link, "keeplinks"]
                        formatted_links.append(formatted_link)
                        direct_links.append(link)  # Keeplinks gehen direkt an JD
                    elif "linkcrypter" in link.lower():
                        formatted_link = [link, "linkcrypter"]
                        formatted_links.append(formatted_link)
                        direct_links.append(link)  # Linkcrypter gehen direkt an JD
                    elif "linkshare" in link.lower():
                        formatted_link = [link, "linkshare"]
                        formatted_links.append(formatted_link)
                        direct_links.append(link)  # Linkshare gehen direkt an JD
                    elif "rapidgator" in link.lower():
                        formatted_link = [link, "rapidgator"]
                        formatted_links.append(formatted_link)
                        direct_links.append(link)  # Direct-Hoster gehen direkt an JD
                    elif "ddownload" in link.lower():
                        formatted_link = [link, "ddownload"]
                        formatted_links.append(formatted_link)
                        direct_links.append(link)  # Direct-Hoster gehen direkt an JD
                    elif "katfile" in link.lower():
                        formatted_link = [link, "katfile"]
                        formatted_links.append(formatted_link)
                        direct_links.append(link)  # Direct-Hoster gehen direkt an JD
                    else:
                        formatted_link = [link, "direct"]
                        formatted_links.append(formatted_link)
                        direct_links.append(link)  # Unbekannte Links gehen direkt an JD
                else:
                    formatted_links.append(link)
                    direct_links.append(link[0] if isinstance(link, list) else link)
            
            debug(f'[DL-DOWNLOAD] Formatted links: {formatted_links}')
            debug(f'[DL-DOWNLOAD] Direct links (bypass CAPTCHA): {direct_links}')
            debug(f'[DL-DOWNLOAD] CAPTCHA links (FileCrypt): {captcha_links}')
            
            # Sende direkte Links (keeplinks, etc.) sofort an JDownloader
            if direct_links:
                info(f'Sending {len(direct_links)} direct container links for "{title}" to JDownloader')
                send_discord_message(shared_state, title=title, case="unprotected", imdb_id=imdb_id, source=url)
                added = shared_state.download_package(direct_links, title, password, package_id)
                if not added:
                    fail(title, package_id, shared_state,
                         reason=f'Failed to add {len(direct_links)} direct links for "{title}" to linkgrabber')
                    success = False
            
            # Nur FileCrypt-Links gehen zum CAPTCHA-Handler
            if captcha_links:
                info(f"CAPTCHA-Solution required for \"{title}\" at: \"{shared_state.values['external_address']}/captcha\"")
                send_discord_message(shared_state, title=title, case="captcha", imdb_id=imdb_id, source=url)
                # Use extracted password if available, otherwise fall back to default password
                final_password = dl_password if dl_password else password
                blob = json.dumps({"title": title, "links": captcha_links, "size_mb": size_mb, "password": final_password})
                debug(f'[DL-DOWNLOAD] Storing protected package with ID: {package_id} and password: {"***" if final_password else "None"}')
                shared_state.values["database"]("protected").update_store(package_id, blob)
        else:
            fail(title, package_id, shared_state,
                 reason=f'Offline / no links found for "{title}" on DL - "{url}"')
            success = False

    elif dt and dt.lower() in url.lower():
        links = get_dt_download_links(shared_state, url, mirror, title)
        if links:
            info(f"Decrypted {len(links)} download links for {title}")
            send_discord_message(shared_state, title=title, case="unprotected", imdb_id=imdb_id, source=url)
            added = shared_state.download_package(links, title, password, package_id)
            if not added:
                fail(title, package_id, shared_state,
                     reason=f'Failed to add {len(links)} links for "{title}" to linkgrabber')
                success = False
        else:
            fail(title, package_id, shared_state,
                 reason=f'Offline / no links found for "{title}" on DT - "{url}"')
            success = False

    elif dw and dw.lower() in url.lower():
        links = get_dw_download_links(shared_state, url, mirror, title)
        info(f'CAPTCHA-Solution required for "{title}" at: "{shared_state.values["external_address"]}/captcha"')
        send_discord_message(shared_state, title=title, case="captcha", imdb_id=imdb_id, source=url)
        blob = json.dumps({"title": title, "links": links, "size_mb": size_mb, "password": password})
        shared_state.values["database"]("protected").update_store(package_id, blob)

    elif mb and mb.lower() in url.lower():
        links = get_mb_download_links(shared_state, url, mirror, title)
        info(f'CAPTCHA-Solution required for "{title}" at: "{shared_state.values["external_address"]}/captcha"')
        send_discord_message(shared_state, title=title, case="captcha", imdb_id=imdb_id, source=url)
        blob = json.dumps({"title": title, "links": links, "size_mb": size_mb, "password": password})
        shared_state.values["database"]("protected").update_store(package_id, blob)

    elif nx and nx.lower() in url.lower():
        links = get_nx_download_links(shared_state, url, title)
        if links:
            info(f"Decrypted {len(links)} download links for {title}")
            send_discord_message(shared_state, title=title, case="unprotected", imdb_id=imdb_id, source=url)
            added = shared_state.download_package(links, title, password, package_id)
            if not added:
                fail(title, package_id, shared_state,
                     reason=f'Failed to add {len(links)} links for "{title}" to linkgrabber')
                success = False
        else:
            fail(title, package_id, shared_state,
                 reason=f'Offline / no links found for "{title}" on NX - "{url}"')
            success = False

    elif sf and sf.lower() in url.lower():
        if url.startswith(f"https://{sf}/external"):  # from interactive search
            url = resolve_sf_redirect(url, shared_state.values["user_agent"])
        elif url.startswith(f"https://{sf}/"):  # from feed search
            data = get_sf_download_links(shared_state, url, mirror, title)
            url = data.get("real_url")
            if not imdb_id:
                imdb_id = data.get("imdb_id")

        if url:
            info(f'CAPTCHA-Solution required for "{title}" at: "{shared_state.values["external_address"]}/captcha"')
            send_discord_message(shared_state, title=title, case="captcha", imdb_id=imdb_id, source=url)
            blob = json.dumps(
                {"title": title, "links": [[url, "filecrypt"]], "size_mb": size_mb, "password": password,
                 "mirror": mirror})
            shared_state.values["database"]("protected").update_store(package_id, blob)
        else:
            fail(title, package_id, shared_state,
                 reason=f'Failed to get download link from SF for "{title}" - "{url}"')
            success = False

    elif sl and sl.lower() in url.lower():
        data = get_sl_download_links(shared_state, url, mirror, title)
        links = data.get("links")
        if not imdb_id:
            imdb_id = data.get("imdb_id")
        if links:
            info(f"Decrypted {len(links)} download links for {title}")
            send_discord_message(shared_state, title=title, case="unprotected", imdb_id=imdb_id, source=url)
            added = shared_state.download_package(links, title, password, package_id)
            if not added:
                fail(title, package_id, shared_state,
                     reason=f'Failed to add {len(links)} links for "{title}" to linkgrabber')
                success = False
        else:
            fail(title, package_id, shared_state,
                 reason=f'Offline / no links found for "{title}" on SL - "{url}"')
            success = False

    elif wd and wd.lower() in url.lower():
        data = get_wd_download_links(shared_state, url, mirror, title)
        links = data.get("links")
        if not imdb_id:
            imdb_id = data.get("imdb_id")
        if links:
            info(f'CAPTCHA-Solution required for "{title}" at: "{shared_state.values["external_address"]}/captcha"')
            send_discord_message(shared_state, title=title, case="captcha", imdb_id=imdb_id, source=url)
            blob = json.dumps({"title": title, "links": links, "size_mb": size_mb, "password": password})
            shared_state.values["database"]("protected").update_store(package_id, blob)
        else:
            fail(title, package_id, shared_state,
                 reason=f'Offline / no links found for "{title}" on WD - "{url}"')
            success = False

    elif "filecrypt".lower() in url.lower():
        info(f'CAPTCHA-Solution required for "{title}" at: "{shared_state.values["external_address"]}/captcha"')
        send_discord_message(shared_state, title=title, case="captcha", imdb_id=imdb_id, source=url)
        blob = json.dumps(
            {"title": title, "links": [[url, "filecrypt"]], "size_mb": size_mb, "password": password, "mirror": mirror})
        shared_state.values["database"]("protected").update_store(package_id, blob)

    else:
        info(f'Could not parse URL for "{title}" - "{url}"')
        success = False

    return {
        "success": success,
        "package_id": package_id,
        "title": title
    }


def fail(title, package_id, shared_state, reason="Offline / no links found"):
    try:
        info(f"Reason for failure: {reason}")
        blob = json.dumps({"title": title, "error": reason})
        stored = shared_state.get_db("failed").store(package_id, json.dumps(blob))
        if stored:
            info(f'Package "{title}" marked as failed!"')
            return True
        else:
            info(f'Failed to mark package "{title}" as failed!"')
            return False
    except Exception as e:
        info(f'Error marking package "{package_id}" as failed: {e}')
        return False
