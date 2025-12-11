![Kuasarr](kuasarr/static/logo-192.png)

# Kuasarr (Quasarr Fork)

[![Docker Hub Version](https://img.shields.io/docker/v/weedo078/kuasarr?label=Docker%20Hub%20Version&logo=docker)](https://hub.docker.com/r/weedo078/kuasarr/tags)
[![Docker Pulls](https://img.shields.io/docker/pulls/weedo078/kuasarr?label=Downloads&logo=docker)](https://hub.docker.com/r/weedo078/kuasarr)

### Quasarr fork with additional hosters (e.g. DL, WX, AD), and an open download API. 

Kuasarr connects JDownloader with Radarr, Sonarr and LazyLibrarian. It also decrypts links protected by CAPTCHAs.

Kuasarr pretends to be both `Newznab Indexer` and `SABnzbd client`. Therefore, do not try to use it with real usenet
indexers or download clients. It simply does not know what NZB or torrent files are.



## Quick Start

Docker Hub: [weedo078/kuasarr](https://hub.docker.com/r/weedo078/kuasarr)

```bash
docker run -d \
  --name kuasarr \
  -p 8080:8080 \
  -v /path/to/config/:/config \
  -e INTERNAL_ADDRESS=http://192.168.0.1:8080 \
  -e EXTERNAL_ADDRESS=http://192.168.0.1:8080 \
  weedo078/kuasarr:latest
```

All configuration, Hostnames, Flaresolverr, etc. lives inside `/config/kuasarr.ini`. Hostnames and FlareSolverr can also be managed via the Web UI. Available image tags are listed on [Docker Hub](https://hub.docker.com/r/weedo078/kuasarr/tags).

## Improvements

- **DeathByCaptcha Integration**: Automatic captcha solving via [DeathByCaptcha](https://deathbycaptcha.com?refid=1237432788a). Configure credentials in `kuasarr.ini` or via environment variables.
- **Hoster Filtering**: Exclude unwanted mirrors directly via the UI.

# Instructions
1. Set up and run [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) 3.4.4 or later.
2. Set up and run [JDownloader 2](https://jdownloader.org/download/index).
3. Follow the next steps.

---

## FlareSolverr
1. Ensure your running FlareSolverr is reachable by Kuasarr.
2. Provide your FlareSolverr URL to Kuasarr during the setup process.
3. The full URL must include the version path, e.g., `http://192.168.1.1:8191/v1`.

---

## Kuasarr

Tell Kuasarr which sites to search for releases. It requires at least one valid source to start up.

> - By default, Kuasarr does **not** know which sites to scrape for download links.  
> - The setup will guide you through the process of providing valid hostnames for Kuasarr to scrape.  
> - Do **not** ask for help here if you do not know which hostnames to use. Picking them is solely your responsibility.  
> - You may check sites like [Pastebin](https://pastebin.com/search?q=hostnames+Quasarr) for user‑submitted suggestions.

---

## JDownloader

1. Ensure your running JDownloader is connected to the My JDownloader service.  
2. Provide your [My‑JDownloader‑Credentials](https://my.jdownloader.org) to Kuasarr during the setup process.

> - Consider setting up a fresh JDownloader before you begin.  
> - JDownloader must be running and available to Kuasarr.  
> - Kuasarr will modify JDownloader’s settings so downloads can be handled by Radarr/Sonarr/LazyLibrarian.  
> - If using Docker, ensure that JDownloader’s download path is available to Radarr/Sonarr/LazyLibrarian with **exactly the same** internal and external path mapping (matching only the external path is not enough).

---

## Radarr / Sonarr

Set up Kuasarr as a **Newznab Indexer** and **SABnzbd Download Client**:

1. **URL**: Use the `URL` from the **API Information** section of the console output (or copy it from the Kuasarr web UI).  
2. **API Key**: Use the `API Key` from the **API Information** section of the console output (or copy it from the Kuasarr web UI).  
3. Leave all other settings at their defaults.

> **Important notice for Sonarr**  
> - Ensure all shows (including anime) are set to the **Standard** series type.  
> - Kuasarr will never find releases for shows set to **Anime / Absolute**.

---

## LazyLibrarian

> **Important notice**
> - This feature is experimental and may not work as expected.
> - Kuasarr cannot help you with metadata issues, missing covers, or other LazyLibrarian problems.
> - Please report issues when one of your hostnames yields results through their website, but not in LazyLibrarian.

Set up Kuasarr as a **SABnzbd+ Downloader**

1. **SABnzbd URL/Port**: Use port and host parts from `URL` found in the **API Information** section of the console output (or copy it from the Kuasarr web UI).  
2. **SABnzbd API Key**: Use the `API Key` from the **API Information** section of the console output (or copy it from the Kuasarr web UI).  
3. **SABnzbd Category**: Use `docs` to ensure LazyLibrarian does not interfere with Radarr/Sonarr.  
4. Press `Test SABnzbd` to verify the connection, then `Save changes`.

Set up Kuasarr as a **Newznab Provider**:
1. **Newznab URL**: Use the `URL` from the **API Information** section of the console output (or copy it from the Kuasarr web UI).
2. **Newznab API** Use the `API Key` from the **API Information** section of the console output (or copy it from the Kuasarr web UI).
3. Press `Test` to verify the connection, then `Save changes`.

Fix the `Importing` settings:
1. Check `Enable OpenLibrary api for book/author information`
2. Select `OpenLibrary` below `Primary Information Source`
2. Under `Import languages` add `, Unknown` (and for German users: `, de, ger, de-DE`).

Fix the `Processing` settings:
1. Under `Folders` add the full Kuasarr download path, typically `/downloads/Kuasarr/`
2. If you do not do this,  processing after the download will fail.

## DeathByCaptcha Configuration

Add your DBC credentials to `kuasarr.ini`:

```ini
[DeathByCaptcha]
# Option 1: Username/Password
username = your_username
password = your_password

# Option 2: Auth Token (recomended)
authtoken = your_auth_token

```

Or use environment variables:

```bash
docker run -d \
  --name kuasarr \
  -p 8080:8080 \
  -v /path/to/config/:/config \
  -e INTERNAL_ADDRESS=http://192.168.0.1:8080 \
  -e DBC_USERNAME=your_username \
  -e DBC_PASSWORD=your_password \
  weedo078/kuasarr:latest
```

Available environment variables:
- `DBC_USERNAME` - DeathByCaptcha username
- `DBC_PASSWORD` - DeathByCaptcha password
- `DBC_AUTHTOKEN` - Alternative: Auth token (instead of username/password)

Get your DBC account at: [deathbycaptcha.com](https://deathbycaptcha.com?refid=1237432788a)

## Install as PWA (Progressive Web App)

Kuasarr can be installed as a standalone app on your device:

1. **Desktop (Chrome/Edge)**: Click the install icon in the address bar or use the browser menu → "Install Kuasarr"
2. **Android**: Open Kuasarr in Chrome, tap the menu (⋮) → "Add to Home screen"
3. **iOS**: Open Kuasarr in Safari, tap Share → "Add to Home Screen"

> **Note**: PWA installation requires HTTPS. If running locally without TLS, use a reverse proxy (e.g., Nginx, Caddy) or access via `localhost`.

## License

- MIT (see `LICENSE`)
- Fork of [`rix1337/quasarr`](https://github.com/rix1337/quasarr)
