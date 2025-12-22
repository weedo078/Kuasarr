---
description: Install Kuasarr on Ultra.cc (userland, no sudo)
---

# Install Kuasarr on Ultra.cc

References used:
- Generic software installation: https://docs.ultra.cc/unofficial-application-installers/generic-software-installation
- Pyenv installer: https://docs.ultra.cc/unofficial-language-installers/install-python-using-pyenv

## 1) Install Python with pyenv (no sudo)
```bash
bash <(wget -qO- https://scripts.ultra.cc/util-v2/LanguageInstaller/Python-Installer/main.sh)
# choose Python 3.9 or 3.11; wait for completion
source ~/.profile   # load pyenv shims
python --version    # should point to ~/.pyenv/shims/python
```

## 2) Create venv and install wheel (from GitHub Releases)
```bash
cd ~/apps/kuasarr
python -m venv .venv-kuasarr-1.8.1
source .venv-kuasarr-1.8.1/bin/activate
pip install --upgrade pip
# example: latest release wheel (adjust if needed)
curl -L -o /tmp/kuasarr-latest.whl "https://github.com/weedo078/kuasarr/releases/latest/download/kuasarr-1.8.1-py3-none-any.whl"
pip install /tmp/kuasarr-latest.whl
```

## 3) Prepare config path pointer
Create `kuasarr.conf` in the Kuasarr working dir with the path to your config folder (single line):
```bash
printf "/home/<user>/apps/kuasarr/config" > /home/<user>/apps/kuasarr/kuasarr.conf
```
Place your `kuasarr.ini` inside that folder (or let Kuasarr generate it).

## 4) Run once to verify
```bash
python -m kuasarr --port 41960 --internal_address http://10.8.0.1:41960
```
Pick a reachable private IP for `--internal_address`. List your candidates and try a private one (e.g. 10.8.0.1 or 172.17.0.1):
```bash
ip -4 addr show scope global | awk '/inet / {print $2}' | cut -d/ -f1
# sample output
# 10.0.0.1
# 172.1.0.1
# ...
```
Use a private IP (10.x / 172.16-31.x) for internal; avoid public addresses for internal callbacks.

## 5) Systemd --user service
Create `~/.config/systemd/user/kuasarr.service`:
```
[Unit]
Description=Kuasarr Service
After=network.target

[Service]
WorkingDirectory=/home/<user>/apps/kuasarr
ExecStart=/home/<user>/apps/kuasarr/.venv-kuasarr-1.8.1/bin/python -m kuasarr --port 41960 --internal_address http://<chosen-ip>:41960
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

Enable + start:
```bash
systemctl --user daemon-reload
systemctl --user enable --now kuasarr.service
```

Logs/status:
```bash
systemctl --user status kuasarr.service
journalctl --user -u kuasarr.service -f
```

If service should survive logout (host policy permitting):
```bash
loginctl enable-linger <user>
```
