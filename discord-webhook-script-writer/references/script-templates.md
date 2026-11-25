# Production Script Templates Catalog

A modular catalog of production-ready, ShellCheck-verified Bash script templates for Discord webhook notifications. In accordance with progressive disclosure, each template is maintained in its own dedicated document with parameter specifications, usage examples, and full source code.

---

## Template Selector Matrix

| Template | Category | Primary Triggers & Use Cases | Key Features | Reference |
| :--- | :--- | :--- | :--- | :--- |
| **CI/CD Deployment Notifier** | CI/CD & DevOps | GitHub Actions, GitLab CI, Jenkins, deployment hooks | Multi-field commit/branch/repo info, dynamic status colors (Green/Red/Yellow), pipeline URL | [ci-cd-deploy-notify.md](../examples/ci-cd-deploy-notify.md) |
| **Cron Server Resource Monitor** | System Administration | VPS health checks, scheduled resource auditing | CPU/RAM/Disk metrics via `top`/`free`/`df`, configurable thresholds, `--only-on-alert` | [cron-server-monitor.md](../examples/cron-server-monitor.md) |
| **Automated Backup Notifier** | Operations & Reliability | Nightly database dumps (`pg_dump`, `mongodump`), archive syncs | Archive size calculation, elapsed duration, failure error log tailing (`tail -n 10`) | [cron-backup-notify.md](../examples/cron-backup-notify.md) |
| **File Attachment & Log Uploader** | Diagnostics & Testing | Test suite crash reports, build artifact uploads, screenshots | `multipart/form-data` upload, `payload_json` embed summary, automatic file size tracking | [file-uploader-notify.md](../examples/file-uploader-notify.md) |
| **Generic Parameterized Embed Alert** | Developer Tooling | Ad-hoc CLI notifications, long-running script wrappers | Custom titles, markdown bodies, severity palettes, user pings (`<@ID>`), silent mode | [generic-embed-alert.md](../examples/generic-embed-alert.md) |

---

## Modular Template Summaries

### 1. [CI/CD Deployment & Build Notifier](../examples/ci-cd-deploy-notify.md)
- **File**: `examples/ci-cd-deploy-notify.md`
- **When to choose**: When the user requests a webhook script for GitHub Actions, GitLab CI, or deployment automation.
- **Inputs**: `--status`, `--repo`, `--branch`, `--commit`, `--actor`, `--run-url`, `--webhook-url`.
- **Formatting**: Rich embed with dynamic green/yellow/red status indicators, metadata fields, and clickable pipeline URL.

### 2. [Cron Server Resource & Health Monitor](../examples/cron-server-monitor.md)
- **File**: `examples/cron-server-monitor.md`
- **When to choose**: When the user wants automated, periodic server capacity monitoring via crontab.
- **Inputs**: `--disk-threshold`, `--mem-threshold`, `--only-on-alert`, `--mention-id`, `--webhook-url`.
- **Formatting**: Displays CPU, RAM, and disk utilization fields. Supports silent suppression on nominal runs and pings an admin User ID on threshold breach.

### 3. [Automated Backup Notifier](../examples/cron-backup-notify.md)
- **File**: `examples/cron-backup-notify.md`
- **When to choose**: When the user needs a completion/error hook for database backups, tar archives, or rsync jobs.
- **Inputs**: `--status`, `--name`, `--file`, `--duration`, `--log-file`, `--webhook-url`.
- **Formatting**: Embed summarizing backup file size and duration. On failure, safely formats and nests the last 10 lines of the error log inside a code block.

### 4. [File Attachment & Log Uploader](../examples/file-uploader-notify.md)
- **File**: `examples/file-uploader-notify.md`
- **When to choose**: When the user needs to upload physical files (test logs, trace dumps, or screenshots) directly to a Discord channel.
- **Inputs**: `--file`, `--title`, `--message`, `--status`, `--webhook-url`.
- **Formatting**: Sends multipart form-data (`-F "payload_json=..." -F "file1=@..."`) pairing an embed with the attached file.

### 5. [Generic Parameterized Embed Alert](../examples/generic-embed-alert.md)
- **File**: `examples/generic-embed-alert.md`
- **When to choose**: For general-purpose alerting, Makefile integrations, or ad-hoc command line notifications.
- **Inputs**: `--title`, `--message`, `--status`, `--mention-id`, `--silent`, `--webhook-url`.
- **Formatting**: Versatile embed supporting arbitrary markdown bodies, severity colors, user mentions, and Discord's silent flag (`flags: 4096`).

---

## Template Adaptation Workflow

When generating a script based on these templates:
1. Read **only** the specific template file needed from `examples/<name>.md`.
2. Customize the parameters, default values, and embed fields to match the user's specific intake requirements.
3. Validate the adapted script with:
   ```bash
   python3 scripts/validate_script.py <script.sh>
   ```
