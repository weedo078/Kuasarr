![Kuasarr](Kuasarr.png)

# Kuasarr (Quasarr Fork)

Quasarr fork with additional hosters (e.g. DL, AD), manual link intake, and an open download API. For in-depth documentation please refer to the original project: [rix1337/quasarr](https://github.com/rix1337/quasarr#readme).

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

All configuration lives inside `/config/kuasarr.ini`. Hostnames and FlareSolverr can be managed via the Web UI. Available image tags are listed on [Docker Hub](https://hub.docker.com/r/weedo078/kuasarr/tags).

## Key Features

- **Manual Link Intake**: Use `/manual-links` in the UI or `POST /api/manual-links` to submit links, optionally set a destination path, and start the job.
- **CaptchaHelper Parallel Mode**: Toggle `[CapHa]` in `kuasarr.ini` or via env vars (`CAPHA_PARALLEL_MODE`, `CAPHA_PARALLEL_MAX`) to process multiple handler jobs simultaneously.
- **Hoster Filtering**: Exclude unwanted mirrors directly via the UI.
- **Encrypted Containers**: Accept Filecrypt/container URLs in the UI, decrypt them, and forward the results to JDownloader.
- **Search (beta)**: Experimental provider search is available but still under active development and may not return results in every case.

Any other functionality (e.g. provider list) matches the Quasarr base and is documented there.

## License

- MIT (see `LICENSE`)
- Copyright (c) 2024 RiX
- Fork of [`rix1337/quasarr`](https://github.com/rix1337/quasarr)

