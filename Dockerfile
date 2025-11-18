FROM alpine:latest
LABEL maintainer="kuasarr"

# install system deps
RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    build-base

# allow pip to manage the system installation (PEP 668)
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN python3 -m pip install --upgrade pip wheel
RUN python3 -m pip install requests

WORKDIR /opt/kuasarr

# copy entire repository into image
COPY . /opt/kuasarr

# Temporarily rewrite version to a PEP 440 compatible form for packaging
RUN python3 - <<'PY'
from pathlib import Path
path = Path('kuasarr/providers/version.py')
text = path.read_text()
path.write_text(text.replace('1.0.dev.1', '1.0.dev1'))
PY

RUN python3 -m pip install --no-cache-dir -r requirements.txt

# install kuasarr from the local checkout (includes our extensions)
RUN python3 -m pip install --no-build-isolation .

# Restore runtime version string in the installed package and source tree
RUN python3 - <<'PY'
import kuasarr, pathlib
installed = pathlib.Path(kuasarr.__file__).parent / 'providers' / 'version.py'
installed.write_text(installed.read_text().replace('1.0.dev1', '1.0.dev.1'))
source = pathlib.Path('/opt/kuasarr/kuasarr/providers/version.py')
source.write_text(source.read_text().replace('1.0.dev1', '1.0.dev.1'))
PY

# cleanup build deps to keep image slim
RUN apk del build-base python3-dev || true

# runtime defaults
VOLUME /config
EXPOSE 8080
ENV PYTHONUNBUFFERED=1 \
    DOCKER="true" \
    INTERNAL_ADDRESS="" \
    EXTERNAL_ADDRESS="" \
    DISCORD="" \
    HOSTNAMES=""

ENTRYPOINT ["sh", "-c", "kuasarr --port=8080 --internal_address=$INTERNAL_ADDRESS --external_address=$EXTERNAL_ADDRESS --discord=$DISCORD --hostnames=$HOSTNAMES"]
