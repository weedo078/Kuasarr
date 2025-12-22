---
description: How to update the Kuasarr Python app (systemd user service)
---

# Kuasarr Update Guide (systemd --user)

## Prerequisites
- Python venv at `~/apps/kuasarr/.venv-kuasarr`
- Systemd user service file: `~/.config/systemd/user/kuasarr.service`

## Steps
1. **Stop service**
   ```bash
   systemctl --user stop kuasarr.service
   ```

2. **Update code / place new wheel**
   - Pull latest code (git) or copy new wheel into the project.

3. **Download latest wheel from GitHub Releases** (example)
   ```bash
   # adjust version/tag/file as needed
   curl -L -o /tmp/kuasarr-latest.whl "https://github.com/weedo078/kuasarr/releases/latest/download/kuasarr-1.8.1-py3-none-any.whl"
   ```

4. **Reinstall wheel** (in venv)
   ```bash
   pip install --force-reinstall /tmp/kuasarr-latest.whl
   ```

5. **Start service**
   ```bash
   systemctl --user start kuasarr.service
   ```

6. **Check status/logs**
   ```bash
   systemctl --user status kuasarr.service
   journalctl --user -u kuasarr.service -f
   ```

## Changing port or internal address
Edit `~/.config/systemd/user/kuasarr.service` (ExecStart line), then:
```bash
systemctl --user daemon-reload
systemctl --user restart kuasarr.service
```

## Keep running after logout (host-dependent)
If required and allowed:
```bash
loginctl enable-linger coronary3409
```
