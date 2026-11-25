# File Attachment & Log Uploader Template

Uploads local files (error logs, test summaries, build artifacts, screenshots) to Discord channels using `multipart/form-data` with an accompanying rich embed summary.

---

## Use Cases
- Attaching detailed crash dumps or diagnostic logs on job failure
- Uploading test coverage or benchmark HTML/text summaries
- Posting automated UI test screenshots
- Archiving small compressed run artifacts in Discord

---

## Parameter Specification

| Option | Long Flag | Environment Variable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-w` | `--webhook-url` | `DISCORD_WEBHOOK_URL` | None (Required) | Target Discord webhook endpoint |
| `-f` | `--file` | None | None (Required) | Path to local file to upload |
| `-t` | `--title` | None | `Artifact Uploaded` | Embed title text |
| `-m` | `--message` | None | None | Additional Markdown message/comment |
| `-s` | `--status` | None | `info` | Visual status: `success`, `warning`, `error`, `info` |
| | `--dry-run` | None | `false` | Prints JSON payload and target file without uploading |
| `-h` | `--help` | None | None | Displays help dialog |

---

## Production Bash Script (`file-uploader.sh`)

```bash
#!/usr/bin/env bash
# file-uploader.sh — Uploads file attachments with rich embed summaries to Discord

set -euo pipefail
IFS=$'\n\t'

TMP_DIR="$(mktemp -d -t discord_upload.XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

show_help() {
  cat << 'EOF'
Usage: file-uploader.sh [OPTIONS]

Upload a local file and embed summary to Discord via webhook.

Options:
  -w, --webhook-url URL    Discord webhook URL (or DISCORD_WEBHOOK_URL)
  -f, --file PATH          Path to file to upload (required)
  -t, --title TEXT         Embed title (default: File Uploaded)
  -m, --message TEXT       Notification description / context
  -s, --status STATUS      Status: success | warning | error | info (default: info)
      --dry-run            Print payload JSON without uploading
  -h, --help               Show this help message
EOF
}

main() {
  if ! command -v jq >/dev/null 2>&1; then
    >&2 echo "Error: jq is required."
    exit 1
  fi

  local cli_url=""
  local file_path=""
  local title="File Uploaded"
  local message=""
  local status="info"
  local dry_run="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -w|--webhook-url) cli_url="$2"; shift 2 ;;
      -f|--file) file_path="$2"; shift 2 ;;
      -t|--title) title="$2"; shift 2 ;;
      -m|--message) message="$2"; shift 2 ;;
      -s|--status) status="$2"; shift 2 ;;
      --dry-run) dry_run="true"; shift ;;
      -h|--help) show_help; exit 0 ;;
      *) >&2 echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
  done

  if [[ -z "$file_path" ]]; then
    if [[ "$dry_run" == "true" ]]; then
      file_path="/path/to/sample.log"
    else
      >&2 echo "Error: --file argument is required."
      show_help
      exit 1
    fi
  fi

  if [[ ! -f "$file_path" && "$dry_run" != "true" ]]; then
    >&2 echo "Error: File not found: $file_path"
    exit 1
  fi

  local webhook_url="${cli_url:-${DISCORD_WEBHOOK_URL:-}}"
  if [[ -z "$webhook_url" && "$dry_run" != "true" ]]; then
    >&2 echo "Error: Webhook URL required via -w/--webhook-url or DISCORD_WEBHOOK_URL"
    exit 1
  fi
  webhook_url="${webhook_url:-https://discord.com/api/webhooks/mock/token}"

  local color=5793266 # Blurple
  case "$status" in
    success) color=5763719 ;;
    warning) color=16705372 ;;
    error)   color=15548997 ;;
    info)    color=5793266 ;;
  esac

  local file_name
  file_name="$(basename "$file_path")"
  local file_size="10 KB"
  if [[ -f "$file_path" ]]; then
    file_size="$(du -h "$file_path" | cut -f1)"
  fi

  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local payload
  payload=$(jq -n \
    --arg title "$title" \
    --arg desc "$message" \
    --arg fname "$file_name" \
    --arg fsize "$file_size" \
    --arg ts "$timestamp" \
    --argjson color "$color" \
    '{
      embeds: [{
        title: $title,
        description: (if $desc != "" then $desc else null end),
        color: $color,
        timestamp: $ts,
        fields: [
          {name: "Attachment Name", value: $fname, inline: true},
          {name: "File Size", value: $fsize, inline: true}
        ],
        footer: {text: "Artifact Uploader Daemon"}
      }]
    }')

  if [[ "$dry_run" == "true" ]]; then
    echo "=== [DRY RUN] Webhook URL ==="
    echo "$webhook_url"
    echo "=== [DRY RUN] Target File ==="
    echo "$file_path ($file_size)"
    echo "=== [DRY RUN] JSON Payload ==="
    echo "$payload" | jq .
    exit 0
  fi

  local resp_file="$TMP_DIR/resp.txt"
  local http_code
  http_code=$(curl -sS -w "%{http_code}" -o "$resp_file" \
    -F "payload_json=$payload" \
    -F "file1=@$file_path;filename=$file_name" \
    "$webhook_url" || echo "000")

  if [[ "$http_code" == "204" || "$http_code" == "200" ]]; then
    echo "File uploaded successfully to Discord."
  else
    >&2 echo "Failed uploading file to Discord (HTTP $http_code)"
    if [[ -s "$resp_file" ]]; then >&2 cat "$resp_file"; >&2 echo ""; fi
    exit 1
  fi
}

main "$@"
```

---

## Example Invocations

### Uploading a Test Failure Log
```bash
./file-uploader.sh \
  --file "/tmp/pytest_run.log" \
  --title "❌ Pytest Suite Failures" \
  --message "3 tests failed out of 124 in latest integration run." \
  --status "error"
```
