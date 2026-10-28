# Bash Scripting Standard for Discord Webhooks

This guide establishes the mandatory engineering standards for crafting reusable, production-ready, ShellCheck-compliant Bash scripts that send notifications to Discord.

---

## 1. Core Script Skeleton

Every generated script must adhere strictly to the following foundational structure:

```bash
#!/usr/bin/env bash
# script_name.sh — Clear, concise description of what the script does

# Strict error handling:
# -e: Exit immediately on non-zero command status
# -u: Treat unset variables as errors
# -o pipefail: Exit status of a pipeline is the last non-zero exit code
set -euo pipefail

# Secure internal field separator to prevent unintended word splitting
IFS=$'\n\t'

# Cleanup handler for temporary files
TMP_DIR="$(mktemp -d -t discord_webhook.XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT
```

---

## 2. Webhook URL Resolution Strategy

### The Dual-Source Rule
A robust script must never force the user into choosing exclusively between an environment variable or a command-line argument. It must support **both**:

1. **CLI Flag (`-w` / `--webhook-url`)**: Highest precedence. Allows ad-hoc overrides, multi-channel routing, and testing.
2. **Environment Variable (`DISCORD_WEBHOOK_URL`)**: Fallback. Cleanest for cron jobs, systemd services, CI/CD runners, and automated scripts without exposing credentials in process tables (`ps aux`).
3. **Failure Guard**: If neither is set, print a clear diagnostic to standard error and exit with code 1.

```bash
WEBHOOK_URL="${CLI_WEBHOOK_URL:-${DISCORD_WEBHOOK_URL:-}}"

if [[ -z "$WEBHOOK_URL" ]]; then
  >&2 echo "Error: Webhook URL must be provided via -w/--webhook-url or DISCORD_WEBHOOK_URL environment variable."
  >&2 echo "Run '$0 --help' for usage instructions."
  exit 1
fi
```

---

## 3. Safe JSON Generation with `jq`

### Why String Interpolation Fails
Never construct JSON payloads through raw bash string interpolation:
```bash
# FRAGILE / DANGEROUS:
# If $MESSAGE contains quotes, newlines, or backslashes, this produces invalid JSON
# or can cause JSON payload injection.
PAYLOAD="{\"content\": \"$MESSAGE\"}" 
```

### The `jq` Gold Standard
Always use `jq -n` to build JSON safely. `jq` automatically escapes quotes, handles multiline text, validates syntax, and brands types accurately:

```bash
build_payload() {
  local title="$1"
  local desc="$2"
  local color="$3"
  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  jq -n \
    --arg title "$title" \
    --arg desc "$desc" \
    --argjson color "$color" \
    --arg ts "$timestamp" \
    '{
      embeds: [{
        title: $title,
        description: $desc,
        color: $color,
        timestamp: $ts,
        footer: {
          text: "Automation Bot"
        }
      }]
    }'
}
```

If `jq` is not guaranteed on target hosts, check for its availability at script startup:
```bash
if ! command -v jq >/dev/null 2>&1; then
  >&2 echo "Error: 'jq' is required to securely format JSON payloads."
  >&2 echo "Install via: sudo apt install jq / brew install jq"
  exit 1
fi
```

---

## 4. Option Parsing & Help Architecture

Use a standard `while [[ $# -gt 0 ]]` loop. This handles both short (`-w`, `-h`) and long (`--webhook-url`, `--dry-run`, `--title`) options safely:

```bash
show_help() {
  cat << 'EOF'
Usage: notify-discord.sh [OPTIONS]

Send formatted alerts and embeds to a Discord channel via webhook.

Options:
  -w, --webhook-url URL    Discord webhook URL (overrides DISCORD_WEBHOOK_URL)
  -t, --title TEXT         Embed title
  -m, --message TEXT       Notification body/description
  -s, --status STATUS      Execution status: success | warning | error | info (default: info)
  -f, --file PATH          Optional file attachment to upload
      --dry-run            Output payload JSON without sending to Discord
  -h, --help               Display this help dialog and exit

Environment Variables:
  DISCORD_WEBHOOK_URL      Default webhook URL if not provided via -w/--webhook-url

Examples:
  # Using environment variable:
  export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
  ./notify-discord.sh --title "Build Passed" --status success

  # Dry run to preview payload:
  ./notify-discord.sh --title "Test" --message "Dry run test" --dry-run
EOF
}
```

---

## 5. cURL Execution & Resilience

Capturing both the HTTP response body and the HTTP response status code cleanly is essential for distinguishing success from errors:

```bash
send_webhook() {
  local webhook_url="$1"
  local payload="$2"
  local file_path="${3:-}"
  local dry_run="${4:-false}"

  if [[ "$dry_run" == "true" ]]; then
    echo "=== [DRY RUN] Webhook URL ==="
    echo "$webhook_url"
    echo "=== [DRY RUN] JSON Payload ==="
    echo "$payload" | jq .
    if [[ -n "$file_path" ]]; then
      echo "=== [DRY RUN] Attachment ==="
      echo "File: $file_path"
    fi
    return 0
  fi

  local resp_file="$TMP_DIR/response.txt"
  local http_code
  local max_retries=3
  local attempt=1

  while [[ $attempt -le $max_retries ]]; do
    if [[ -n "$file_path" && -f "$file_path" ]]; then
      http_code=$(curl -sS -w "%{http_code}" -o "$resp_file" \
        -F "payload_json=$payload" \
        -F "file1=@$file_path" \
        "$webhook_url" || echo "000")
    else
      http_code=$(curl -sS -w "%{http_code}" -o "$resp_file" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$webhook_url" || echo "000")
    fi

    # 204 No Content is standard Discord success; 200 OK occurs if ?wait=true
    if [[ "$http_code" == "204" || "$http_code" == "200" ]]; then
      return 0
    elif [[ "$http_code" == "429" ]]; then
      local retry_after
      retry_after=$(jq -r '.retry_after // 2' "$resp_file" 2>/dev/null || echo "2")
      >&2 echo "[Warning] Rate limited by Discord (HTTP 429). Waiting ${retry_after}s before retry $attempt/$max_retries..."
      sleep "$retry_after"
      attempt=$((attempt + 1))
    elif [[ "$http_code" =~ ^5 ]]; then
      >&2 echo "[Warning] Discord server error (HTTP $http_code). Retrying in 2s..."
      sleep 2
      attempt=$((attempt + 1))
    else
      >&2 echo "Error: Discord webhook request failed with HTTP $http_code"
      if [[ -s "$resp_file" ]]; then
        >&2 cat "$resp_file"
        >&2 echo ""
      fi
      return 1
    fi
  done

  >&2 echo "Error: Failed to deliver Discord webhook after $max_retries attempts."
  return 1
}
```

---

## 6. ShellCheck Hygiene & Common Gotchas

Every generated script must pass `shellcheck -s bash` with zero warnings. Keep these frequent pitfalls in mind:

1. **SC2155: Declare and assign separately in `local`**:
   ```bash
   # WRONG: Masks the return code of the command substitution
   local output=$(date)

   # CORRECT:
   local output
   output="$(date)"
   ```

2. **SC2086: Double quote all variable expansions**:
   ```bash
   # WRONG:
   curl -H Content-Type: application/json -d $payload $url

   # CORRECT:
   curl -H "Content-Type: application/json" -d "$payload" "$url"
   ```

3. **Conditionals**: Always use double brackets `[[ ... ]]` instead of legacy single brackets `[ ... ]`.
4. **Isolated Entry Point**: Always isolate script execution in a `main()` function and call `main "$@"` as the final line.
