# cronwatch

Lightweight daemon that monitors cron job execution, logs durations, and sends alerts on failures or unexpected silences.

---

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/yourname/cronwatch.git && cd cronwatch && pip install .
```

---

## Usage

Start the daemon and point it at your config file:

```bash
cronwatch start --config /etc/cronwatch/config.yaml
```

Example `config.yaml`:

```yaml
jobs:
  backup-db:
    schedule: "0 2 * * *"
    timeout: 300
    alert_on_silence: true
    notify:
      email: ops@example.com

  sync-files:
    schedule: "*/15 * * * *"
    timeout: 60
```

Wrap your cron commands to report status back to the daemon:

```bash
# In your crontab
*/15 * * * * cronwatch run --job sync-files -- /usr/local/bin/sync.sh
```

View logs and job history:

```bash
cronwatch status
cronwatch logs --job backup-db --tail 50
```

---

## Configuration

| Key | Description | Default |
|-----|-------------|---------|
| `schedule` | Cron expression for expected run time | required |
| `timeout` | Max allowed duration in seconds | `3600` |
| `alert_on_silence` | Alert if job does not run on schedule | `false` |

---

## License

MIT © 2024 yourname