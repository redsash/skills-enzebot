# Automated Backup Notifier Template

Monitors and reports the completion of backup jobs (`pg_dump`, `tar`, `rsync`, `borg`). Inspects backup archive size, records duration, and extracts log tails automatically when jobs fail.

---

## Use Cases
- PostgreSQL / MySQL / MongoDB database dump completion reporting
- Nightly filesystem and user home archive verification
- Off-site rsync / rclone cloud synchronization reports
- Failure diagnosis with embedded recent error logs

---

## Parameter Specification

| Option | Long Flag | Environment Variable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-w` | `--webhook-url` | `DISCORD_WEBHOOK_URL` | None (Required) | Target Discord webhook endpoint |
| `-s` | `--status` | None | `success` | Backup outcome: `success` or `failed` |
| `-n` | `--name` | None | `Database Backup` | Human-readable identifier for the backup job |
| `-f` | `--file` | None | None | Path to generated backup archive (to inspect file size) |
| `-d` | `--duration` | None | `0s` | Elapsed execution duration string (e.g. `45s`, `3m 12s`) |
| `-l` | `--log-file` | None | None | Path to log file (extracts last 10 lines on failure) |
| | `--dry-run` | None | `false` | Prints JSON payload to stdout without sending |
| `-h` | `--help` | None | None | Displays help dialog |

---

## Production Bash Script (`cron-backup-notify.sh`)

```bash
#!/usr/bin/env bash
# cron-backup-notify.sh — Posts backup status, size, duration, and error excerpts to Discord

set -euo pipefail
IFS=$'\n\t'

TMP_DIR="$(mktemp -d -t discord_backup.XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

show_help() {
  cat << 'EOF'
Usage: cron-backup-notify.sh [OPTIONS]

Options:
  -w, --webhook-url URL       Discord webhook URL (or DISCORD_WEBHOOK_URL)
  -s, --status STATUS         Status: success | failed
  -n, --name JOB_NAME         Backup name/identifier (e.g. Postgres-Production)
  -f, --file PATH             Path to backup archive (to inspect size)
  -d, --duration SECONDS      Duration of the backup run in seconds
  -l, --log-file PATH         Path to error log (tails last 10 lines on failure)
      --dry-run               Print payload JSON without sending
  -h, --help                  Show this help message
EOF
}

main() {
  if ! command -v jq >/dev/null 2>&1; then
    >&2 echo "Error: jq is required."
    exit 1
  fi

  local cli_url=""
  local status="success"
  local job_name="Database Backup"
  local backup_file=""
  local duration="0s"
  local log_file=""
  local dry_run="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -w|--webhook-url) cli_url="$2"; shift 2 ;;
      -s|--status) status="$2"; shift 2 ;;
      -n|--name) job_name="$2"; shift 2 ;;
      -f|--file) backup_file="$2"; shift 2 ;;
      -d|--duration) duration="$2"; shift 2 ;;
      -l|--log-file) log_file="$2"; shift 2 ;;
      --dry-run) dry_run="true"; shift ;;
      -h|--help) show_help; exit 0 ;;
      *) >&2 echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
  done

  local webhook_url="${cli_url:-${DISCORD_WEBHOOK_URL:-}}"
  if [[ -z "$webhook_url" && "$dry_run" != "true" ]]; then
    >&2 echo "Error: Webhook URL required via -w/--webhook-url or DISCORD_WEBHOOK_URL"
    exit 1
  fi
  webhook_url="${webhook_url:-https://discord.com/api/webhooks/mock/token}"

  local backup_size="N/A"
  if [[ -n "$backup_file" && -f "$backup_file" ]]; then
    backup_size=$(du -h "$backup_file" | cut -f1)
  fi

  local log_tail=""
  if [[ "$status" == "failed" && -n "$log_file" && -f "$log_file" ]]; then
    log_tail="$(tail -n 10 "$log_file")"
  fi

  local title="💾 Backup Complete: $job_name"
  local color=5763719 # Green
  if [[ "$status" == "failed" ]]; then
    title="❌ Backup Failed: $job_name"
    color=15548997 # Red
  fi

  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local payload
  payload=$(jq -n \
    --arg title "$title" \
    --arg job "$job_name" \
    --arg status "$status" \
    --arg size "$backup_size" \
    --arg dur "$duration" \
    --arg log_tail "$log_tail" \
    --arg ts "$timestamp" \
    --argjson color "$color" \
    '{
      embeds: [{
        title: $title,
        color: $color,
        timestamp: $ts,
        fields: [
          {name: "Job", value: $job, inline: true},
          {name: "Status", value: $status, inline: true},
          {name: "Archive Size", value: $size, inline: true},
          {name: "Duration", value: $dur, inline: true}
        ] + (if $log_tail != "" then [{name: "Error Log Tail", value: ("```\n" + $log_tail + "\n```"), inline: false}] else [] end),
        footer: {text: "Automated Backup Daemon"}
      }]
    }')

  if [[ "$dry_run" == "true" ]]; then
    echo "=== [DRY RUN] Webhook URL ==="
    echo "$webhook_url"
    echo "=== [DRY RUN] JSON Payload ==="
    echo "$payload" | jq .
    exit 0
  fi

  local resp_file="$TMP_DIR/resp.txt"
  local http_code
  http_code=$(curl -sS -w "%{http_code}" -o "$resp_file" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "$webhook_url" || echo "000")

  if [[ "$http_code" == "204" || "$http_code" == "200" ]]; then
    echo "Backup report sent to Discord."
  else
    >&2 echo "Failed sending backup webhook (HTTP $http_code)"
    exit 1
  fi
}

main "$@"
```

---

## Example Invocations

### 1. In a Nightly Backup Bash Script
```bash
START_TIME=$(date +%s)
BACKUP_ARCHIVE="/var/backups/postgres-$(date +%Y%m%d).sql.gz"
LOG_FILE="/var/log/pg_backup.log"

if pg_dump -U postgres myapp | gzip > "$BACKUP_ARCHIVE" 2>"$LOG_FILE"; then
  ELAPSED="$(($(date +%s) - START_TIME))s"
  ./cron-backup-notify.sh \
    --name "PostgreSQL Production" \
    --status "success" \
    --file "$BACKUP_ARCHIVE" \
    --duration "$ELAPSED"
else
  ELAPSED="$(($(date +%s) - START_TIME))s"
  ./cron-backup-notify.sh \
    --name "PostgreSQL Production" \
    --status "failed" \
    --duration "$ELAPSED" \
    --log-file "$LOG_FILE"
fi
```
