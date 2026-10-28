# Generic Parameterized Embed Alert Template

A versatile, multi-purpose CLI alert script for ad-hoc terminal invocations, shell scripts, and system alerts. Supports custom embed titles, markdown bodies, dynamic severity color palettes, and Discord user mentions.

---

## Use Cases
- Ad-hoc alerts dispatched from bash scripts, Makefile targets, or wrapper utilities
- Notification hooks in long-running compilation or ML training tasks
- General-purpose alerting for developer environments
- Rapid prototyping of new Discord notification types

---

## Parameter Specification

| Option | Long Flag | Environment Variable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-w` | `--webhook-url` | `DISCORD_WEBHOOK_URL` | None (Required) | Target Discord webhook endpoint |
| `-t` | `--title` | None | `System Notification` | Embed title text |
| `-m` | `--message` | None | None | Notification description / body text |
| `-s` | `--status` | None | `info` | Visual status: `success`, `warning`, `error`, `info` |
| | `--mention-id` | None | None | Discord User ID to mention in message |
| | `--silent` | None | `false` | Sets `flags: 4096` to suppress sounds and mobile pings |
| | `--dry-run` | None | `false` | Prints JSON payload to stdout without sending |
| `-h` | `--help` | None | None | Displays help dialog |

---

## Production Bash Script (`discord-alert.sh`)

```bash
#!/usr/bin/env bash
# discord-alert.sh — General-purpose parameterized Discord alert script

set -euo pipefail
IFS=$'\n\t'

TMP_DIR="$(mktemp -d -t discord_alert.XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

show_help() {
  cat << 'EOF'
Usage: discord-alert.sh [OPTIONS]

Send a formatted embed alert to a Discord channel via webhook.

Options:
  -w, --webhook-url URL    Discord webhook URL (or DISCORD_WEBHOOK_URL)
  -t, --title TEXT         Embed title (default: System Notification)
  -m, --message TEXT       Notification body description
  -s, --status STATUS      Status: success | warning | error | info (default: info)
      --mention-id ID      Discord User ID to mention
      --silent             Suppress push notifications and badges (flags: 4096)
      --dry-run            Print payload JSON without sending
  -h, --help               Show this help message
EOF
}

main() {
  if ! command -v jq >/dev/null 2>&1; then
    >&2 echo "Error: jq is required."
    exit 1
  fi

  local cli_url=""
  local title="System Notification"
  local message=""
  local status="info"
  local mention_id=""
  local silent="false"
  local dry_run="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -w|--webhook-url) cli_url="$2"; shift 2 ;;
      -t|--title) title="$2"; shift 2 ;;
      -m|--message) message="$2"; shift 2 ;;
      -s|--status) status="$2"; shift 2 ;;
      --mention-id) mention_id="$2"; shift 2 ;;
      --silent) silent="true"; shift ;;
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

  local color=5793266 # Blurple
  case "$status" in
    success) color=5763719 ;; # Green
    warning) color=16705372 ;; # Yellow
    error)   color=15548997 ;; # Red
    info)    color=5793266 ;; # Blurple
  esac

  local content=""
  if [[ -n "$mention_id" ]]; then
    content="<@$mention_id>"
  fi

  local flags=0
  if [[ "$silent" == "true" ]]; then
    flags=4096
  fi

  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local payload
  payload=$(jq -n \
    --arg title "$title" \
    --arg desc "$message" \
    --arg content "$content" \
    --arg ts "$timestamp" \
    --argjson color "$color" \
    --argjson flags "$flags" \
    '{
      content: (if $content != "" then $content else null end),
      flags: (if $flags > 0 then $flags else null end),
      embeds: [{
        title: $title,
        description: (if $desc != "" then $desc else null end),
        color: $color,
        timestamp: $ts,
        footer: {text: "Discord Alert Bot"}
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
    echo "Alert delivered successfully."
  else
    >&2 echo "Failed to deliver Discord alert (HTTP $http_code)"
    if [[ -s "$resp_file" ]]; then >&2 cat "$resp_file"; >&2 echo ""; fi
    exit 1
  fi
}

main "$@"
```

---

## Example Invocations

### 1. Alerting after Long Build Task
```bash
make build-production && ./discord-alert.sh \
  --title "Build Complete" \
  --message "Production artifact built successfully." \
  --status "success"
```

### 2. Silent Routine Sync Ping
```bash
./discord-alert.sh \
  --title "Routine Cache Invalidation" \
  --message "CDN edge caches cleared." \
  --status "info" \
  --silent
```
