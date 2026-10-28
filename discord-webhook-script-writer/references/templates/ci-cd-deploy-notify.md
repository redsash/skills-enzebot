# CI/CD Deployment & Build Notifier Template

Posts structured, multi-field deployment and build status embeds to Discord. Designed for seamless execution in GitHub Actions, GitLab CI, Jenkins, and webhook deployment scripts.

---

## Use Cases
- GitHub Actions workflow completion hooks (`job.status`)
- GitLab CI/CD pipeline stage notifications
- Automated Kubernetes/Docker production deployment alerts
- Staging and preview environment release broadcasts

---

## Parameter Specification

| Option | Long Flag | Environment Variable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-w` | `--webhook-url` | `DISCORD_WEBHOOK_URL` | None (Required) | Target Discord webhook endpoint |
| `-s` | `--status` | `CI_STATUS` | `success` | Build/Deploy state: `success`, `failure`, or `in-progress` |
| `-r` | `--repo` | `CI_REPO` | `unknown/repo` | Repository identifier (e.g., `owner/repo`) |
| `-b` | `--branch` | `CI_BRANCH` | `main` | Target git branch |
| `-c` | `--commit` | `CI_COMMIT_SHA` | `N/A` | Git commit hash or short SHA |
| `-a` | `--actor` | `CI_ACTOR` | `CI Runner` | Username or author triggering the run |
| `-u` | `--run-url` | `CI_PIPELINE_URL` | None | Link to the pipeline run logs |
| | `--dry-run` | None | `false` | Prints JSON payload to stdout without sending |
| `-h` | `--help` | None | None | Displays help dialog |

---

## Production Bash Script (`ci-deploy-notify.sh`)

```bash
#!/usr/bin/env bash
# ci-deploy-notify.sh — Sends structured CI/CD deployment status embeds to Discord

set -euo pipefail
IFS=$'\n\t'

TMP_DIR="$(mktemp -d -t discord_ci.XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

show_help() {
  cat << 'EOF'
Usage: ci-deploy-notify.sh [OPTIONS]

Options:
  -w, --webhook-url URL    Discord webhook URL (or DISCORD_WEBHOOK_URL)
  -s, --status STATUS      Status: success | failure | in-progress (default: success)
  -r, --repo REPO          Repository name (e.g. org/repo)
  -b, --branch BRANCH      Git branch name (default: main)
  -c, --commit SHA         Commit hash / identifier
  -a, --actor NAME         Author / actor triggering deployment
  -u, --run-url URL        URL link to CI/CD pipeline run
      --dry-run            Print payload JSON without sending
  -h, --help               Show this help message
EOF
}

build_payload() {
  local status="$1"
  local repo="$2"
  local branch="$3"
  local commit="$4"
  local actor="$5"
  local run_url="$6"
  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local color=5793266 # Blurple default
  local title="🚀 Deployment Status: $status"
  case "$status" in
    success)
      color=5763719 # Green
      title="✅ Deployment Succeeded: $repo"
      ;;
    failure)
      color=15548997 # Red
      title="❌ Deployment Failed: $repo"
      ;;
    in-progress)
      color=16705372 # Yellow
      title="⏳ Deployment Started: $repo"
      ;;
  esac

  jq -n \
    --arg title "$title" \
    --arg repo "$repo" \
    --arg branch "$branch" \
    --arg commit "$commit" \
    --arg actor "$actor" \
    --arg run_url "$run_url" \
    --arg ts "$timestamp" \
    --argjson color "$color" \
    '{
      embeds: [{
        title: $title,
        url: (if $run_url != "" then $run_url else null end),
        color: $color,
        timestamp: $ts,
        fields: [
          {name: "Repository", value: $repo, inline: true},
          {name: "Branch", value: $branch, inline: true},
          {name: "Commit", value: (if $commit != "" then $commit else "N/A" end), inline: true},
          {name: "Triggered By", value: (if $actor != "" then $actor else "CI Runner" end), inline: true}
        ],
        footer: {text: "CI/CD Deployment Automation"}
      }]
    }'
}

send_webhook() {
  local url="$1"
  local payload="$2"
  local dry_run="$3"

  if [[ "$dry_run" == "true" ]]; then
    echo "=== [DRY RUN] Webhook URL ==="
    echo "$url"
    echo "=== [DRY RUN] JSON Payload ==="
    echo "$payload" | jq .
    return 0
  fi

  local resp_file="$TMP_DIR/resp.txt"
  local http_code
  http_code=$(curl -sS -w "%{http_code}" -o "$resp_file" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "$url" || echo "000")

  if [[ "$http_code" == "204" || "$http_code" == "200" ]]; then
    echo "Notification sent successfully."
    return 0
  else
    >&2 echo "Error: Failed to send Discord webhook (HTTP $http_code)"
    if [[ -s "$resp_file" ]]; then >&2 cat "$resp_file"; >&2 echo ""; fi
    return 1
  fi
}

main() {
  if ! command -v jq >/dev/null 2>&1; then
    >&2 echo "Error: jq is required."
    exit 1
  fi

  local cli_url=""
  local status="success"
  local repo="unknown/repo"
  local branch="main"
  local commit=""
  local actor=""
  local run_url=""
  local dry_run="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -w|--webhook-url) cli_url="$2"; shift 2 ;;
      -s|--status) status="$2"; shift 2 ;;
      -r|--repo) repo="$2"; shift 2 ;;
      -b|--branch) branch="$2"; shift 2 ;;
      -c|--commit) commit="$2"; shift 2 ;;
      -a|--actor) actor="$2"; shift 2 ;;
      -u|--run-url) run_url="$2"; shift 2 ;;
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

  local payload
  payload="$(build_payload "$status" "$repo" "$branch" "$commit" "$actor" "$run_url")"
  send_webhook "$webhook_url" "$payload" "$dry_run"
}

main "$@"
```

---

## Example Invocations

### 1. Manual CLI / Dry Run
```bash
./ci-deploy-notify.sh \
  --repo "acme/web-portal" \
  --branch "release/2.4.0" \
  --commit "8fa21e9" \
  --actor "octocat" \
  --status "success" \
  --dry-run
```

### 2. GitHub Actions Step
```yaml
- name: Notify Discord of Deployment
  if: always()
  env:
    DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
  run: |
    ./ci-deploy-notify.sh \
      --repo "${{ github.repository }}" \
      --branch "${{ github.ref_name }}" \
      --commit "${{ github.sha }}" \
      --actor "${{ github.actor }}" \
      --run-url "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}" \
      --status "${{ job.status == 'success' && 'success' || 'failure' }}"
```
