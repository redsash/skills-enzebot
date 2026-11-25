# Cron Server Resource & Health Monitor Template

Monitors CPU, memory, and disk capacity via cron and delivers structured embeds to Discord. Features configurable alert thresholds, optional user pings on alert, and silent execution when health metrics are nominal.

---

## Use Cases
- Scheduled cron tasks (`*/10 * * * *`) on Linux production VPS/bare-metal servers
- Low-overhead disk capacity monitoring for media/database servers
- Memory leak detection and warning alerts
- Proactive alert pings before server out-of-memory crashes

---

## Parameter Specification

| Option | Long Flag | Environment Variable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-w` | `--webhook-url` | `DISCORD_WEBHOOK_URL` | None (Required) | Target Discord webhook endpoint |
| | `--disk-threshold` | None | `85` | Disk warning threshold percentage |
| | `--mem-threshold` | None | `90` | Memory warning threshold percentage |
| | `--only-on-alert` | None | `false` | Suppresses webhook when all metrics are nominal |
| | `--mention-id` | None | None | Discord User ID to ping on critical threshold breaches |
| | `--dry-run` | None | `false` | Prints JSON payload to stdout without sending |
| `-h` | `--help` | None | None | Displays help dialog |

---

## Production Bash Script (`cron-server-monitor.sh`)

```bash
#!/usr/bin/env bash
# cron-server-monitor.sh — Monitors CPU, memory, and disk usage and alerts Discord

set -euo pipefail
IFS=$'\n\t'

TMP_DIR="$(mktemp -d -t discord_monitor.XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

show_help() {
  cat << 'EOF'
Usage: cron-server-monitor.sh [OPTIONS]

Options:
  -w, --webhook-url URL        Discord webhook URL (or DISCORD_WEBHOOK_URL)
      --disk-threshold PCT     Disk warning threshold percentage (default: 85)
      --mem-threshold PCT      Memory warning threshold percentage (default: 90)
      --only-on-alert          Only send notification if a threshold is exceeded
      --mention-id ID          Discord User ID to ping on critical alerts
      --dry-run                Print payload JSON without sending
  -h, --help                   Show this help message
EOF
}

main() {
  if ! command -v jq >/dev/null 2>&1; then
    >&2 echo "Error: jq is required."
    exit 1
  fi

  local cli_url=""
  local disk_threshold=85
  local mem_threshold=90
  local only_on_alert="false"
  local mention_id=""
  local dry_run="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -w|--webhook-url) cli_url="$2"; shift 2 ;;
      --disk-threshold) disk_threshold="$2"; shift 2 ;;
      --mem-threshold) mem_threshold="$2"; shift 2 ;;
      --only-on-alert) only_on_alert="true"; shift ;;
      --mention-id) mention_id="$2"; shift 2 ;;
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

  local hostname
  hostname="$(uname -n)"

  # Gather system metrics
  local disk_usage
  disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
  local mem_usage
  mem_usage=$(free | awk '/Mem:/ {printf "%.0f", ($3/$2)*100}')
  local cpu_idle
  cpu_idle=$(top -bn1 | awk -F',' '/Cpu\(s\)/ {for(i=1;i<=NF;i++) if($i ~ /id/) {gsub(/[^0-9.]/,"",$i); print $i}}')
  cpu_idle="${cpu_idle:-50.0}"
  local cpu_usage
  cpu_usage=$(awk "BEGIN {printf \"%.0f\", 100 - $cpu_idle}")

  local is_alert="false"
  if [[ "$disk_usage" -ge "$disk_threshold" ]]; then
    is_alert="true"
  fi
  if [[ "$mem_usage" -ge "$mem_threshold" ]]; then
    is_alert="true"
  fi

  if [[ "$only_on_alert" == "true" && "$is_alert" != "true" ]]; then
    echo "All metrics nominal. Suppressing notification (--only-on-alert enabled)."
    exit 0
  fi

  local title="📊 Server Health Status: $hostname"
  local color=5763719 # Green
  local content=""
  if [[ "$is_alert" == "true" ]]; then
    title="⚠️ Resource Alert: $hostname"
    color=15548997 # Red
    if [[ -n "$mention_id" ]]; then
      content="<@$mention_id> System resource threshold exceeded!"
    fi
  fi

  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local payload
  payload=$(jq -n \
    --arg title "$title" \
    --arg content "$content" \
    --arg host "$hostname" \
    --arg disk "${disk_usage}%" \
    --arg mem "${mem_usage}%" \
    --arg cpu "${cpu_usage}%" \
    --arg ts "$timestamp" \
    --argjson color "$color" \
    '{
      content: (if $content != "" then $content else null end),
      embeds: [{
        title: $title,
        color: $color,
        timestamp: $ts,
        fields: [
          {name: "Host", value: $host, inline: true},
          {name: "CPU Usage", value: $cpu, inline: true},
          {name: "Memory Usage", value: $mem, inline: true},
          {name: "Disk Usage (/)", value: $disk, inline: true}
        ],
        footer: {text: "Server Health Monitor"}
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
    echo "Server health notification delivered."
  else
    >&2 echo "Error delivering webhook (HTTP $http_code)"
    exit 1
  fi
}

main "$@"
```

---

## Example Invocations

### 1. Crontab Setup (Every 15 minutes, alerts only)
```cron
# /etc/cron.d/discord-monitor or crontab -e
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/12345/abcdef..."

*/15 * * * * /opt/scripts/cron-server-monitor.sh --only-on-alert --mention-id "123456789012345678" >> /var/log/discord-monitor.log 2>&1
```

### 2. Manual Health Check Run
```bash
./cron-server-monitor.sh --disk-threshold 80 --mem-threshold 85 --dry-run
```
