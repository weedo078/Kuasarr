FROM alpine:latest
LABEL maintainer="kuasarr"

# install system deps
RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    build-base \
    zlib-dev

# allow pip to manage the system installation (PEP 668)
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# discrete virtualenv to keep patched toolchain versions isolated
RUN python3 -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN pip install --no-cache-dir --upgrade pip==25.3 setuptools==78.1.1 wheel
RUN pip install --no-cache-dir requests

WORKDIR /opt/kuasarr

# copy entire repository into image
COPY . /opt/kuasarr

# Temporarily rewrite version to a PEP 440 compatible form for packaging
RUN python3 - <<'PY'
from pathlib import Path
path = Path('kuasarr/providers/version.py')
text = path.read_text()
path.write_text(text.replace('1.3.0', '1.3.0'))
PY

RUN pip install --no-cache-dir -r requirements.txt

# install kuasarr from the local checkout (includes our extensions)
RUN pip install --no-build-isolation .

# Restore runtime version string in the installed package and source tree
RUN python3 - <<'PY'
import kuasarr, pathlib
installed = pathlib.Path(kuasarr.__file__).parent / 'providers' / 'version.py'
installed.write_text(installed.read_text().replace('1.3.0', '1.3.0'))
source = pathlib.Path('/opt/kuasarr/kuasarr/providers/version.py')
source.write_text(source.read_text().replace('1.3.0', '1.3.0'))
PY

# cleanup build deps to keep image slim
RUN apk del build-base python3-dev zlib-dev || true

# runtime defaults
VOLUME /config
EXPOSE 9999
ENV PYTHONUNBUFFERED=1 \
    DOCKER="true" \
    INTERNAL_ADDRESS="" \
    EXTERNAL_ADDRESS="" \
    DISCORD="" \
    HOSTNAMES=""

ENTRYPOINT ["sh", "-c", "kuasarr --port=9999 --internal_address=$INTERNAL_ADDRESS --external_address=$EXTERNAL_ADDRESS --discord=$DISCORD --hostnames=$HOSTNAMES"]
