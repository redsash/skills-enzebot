# Discord Webhook API & curl Reference

Technical reference for sending formatted Discord messages, rich embeds, mentions, and file attachments using `curl`.

---

## 1. Webhook URL Format & Authentication

Discord webhooks require no API keys or Bearer tokens. All authentication is encapsulated within the webhook URL:

```text
https://discord.com/api/webhooks/<WEBHOOK_ID>/<WEBHOOK_TOKEN>
```

- **Security**: Treat this URL as a private credential with write permissions to the channel.
- Never hardcode the URL in public repositories or unencrypted scripts.
- Support both `--webhook-url` CLI parameter and the `DISCORD_WEBHOOK_URL` environment variable.

---

## 2. HTTP Endpoints & Query Parameters

| Method | Endpoint | Query Param | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/webhooks/{id}/{token}` | `?wait=true` | Returns full message JSON object (`200 OK`) instead of empty body (`204 No Content`). |
| `POST` | `/api/webhooks/{id}/{token}` | `?thread_id={thread_id}` | Posts directly into a forum channel thread or existing text thread. |

---

## 3. Top-Level JSON Payload Specification

```json
{
  "content": "Message string up to 2000 characters",
  "username": "Custom Sender Name (up to 80 chars)",
  "avatar_url": "https://example.com/avatar.png",
  "tts": false,
  "embeds": [ /* array of up to 10 embed objects */ ],
  "allowed_mentions": {
    "parse": ["users", "roles", "everyone"],
    "users": ["123456789012345678"],
    "roles": ["987654321098765432"]
  },
  "flags": 4096
}
```

### Key Flags
- `flags: 4096` (`1 << 12`): **SUPPRESS_NOTIFICATIONS** (Silent message). The message appears in the channel without playing a sound, badge, or pushing a mobile notification.

---

## 4. Rich Embed Object Specification

Discord allows up to **10 embeds per message**. The combined character total across all embeds in a single message cannot exceed **6,000 characters**.

```json
{
  "title": "Alert Title (up to 256 characters)",
  "description": "Markdown body text (up to 4096 characters)",
  "url": "https://example.com/target-link",
  "color": 5763719,
  "timestamp": "2026-10-27T20:00:00.000Z",
  "footer": {
    "text": "Footer text (up to 2048 characters)",
    "icon_url": "https://example.com/footer-icon.png"
  },
  "thumbnail": {
    "url": "https://example.com/thumb.png"
  },
  "image": {
    "url": "https://example.com/main-image.png"
  },
  "author": {
    "name": "Author / System Name (up to 256 characters)",
    "url": "https://example.com/author",
    "icon_url": "https://example.com/author-icon.png"
  },
  "fields": [
    {
      "name": "Field Title (up to 256 characters)",
      "value": "Field content (up to 1024 characters)",
      "inline": true
    }
  ]
}
```

### Embed Constraints Table

| Component | Max Length | Notes |
| :--- | :--- | :--- |
| `title` | 256 characters | Supports plain text |
| `description` | 4,096 characters | Supports standard Discord Markdown |
| `fields` | 25 fields max | Up to 3 inline fields per row in desktop client |
| `fields[].name` | 256 characters | Cannot be empty or whitespace only |
| `fields[].value` | 1,024 characters | Supports Discord Markdown |
| `footer.text` | 2,048 characters | Plain text |
| `author.name` | 256 characters | Plain text |
| Total Embed Characters | 6,000 characters | Cumulative across all title, desc, fields, footer, author |

---

## 5. Embed Decimal Colors Reference

Discord colors are represented as 24-bit decimal integers (`0` to `16,777,215`).

### Color Conversion in Bash
```bash
# Convert HEX RRGGBB to Decimal:
HEX="5865F2" # Discord Blurple
DECIMAL=$((16#$HEX)) # 5793266
```

### Standard Status Colors
| State | Hex | Decimal | Suggested Usage |
| :--- | :--- | :--- | :--- |
| **Success / Healthy** | `#57F287` / `#2ECC71` | `5763719` / `3066993` | Successful deploys, passed backups, normal metrics |
| **Danger / Critical** | `#ED4245` / `#E74C3C` | `15548997` / `15158332` | Failures, exceptions, high disk/CPU threshold alerts |
| **Warning / Caution** | `#FEE75C` / `#F1C40F` | `16705372` / `15844367` | Retrying jobs, degrading health, nearing capacity |
| **Info / Notice** | `#5865F2` / `#3498DB` | `5793266` / `3447003` | Informational updates, build in progress, status pings |
| **Neutral / Muted** | `#4F545C` / `#2F3136` | `5199964` / `3092790` | Routine logs, skipped steps, silent background syncs |

---

## 6. Mentions Syntax & Allowed Mentions

To trigger mobile/desktop notification highlights for specific teams or users:

| Mention Type | Syntax | Note |
| :--- | :--- | :--- |
| **User Mention** | `<@123456789012345678>` | Replaced with `@Username` |
| **Role Mention** | `<@&987654321098765432>` | Replaced with `@Role` |
| **Channel Mention** | `<#112233445566778899>` | Clickable link to channel |
| **Everyone / Here** | `@everyone` or `@here` | Must be explicitly enabled in `allowed_mentions` |

### Allowed Mentions Safety
Discord allows restricting mention permissions to prevent accidental server-wide pings:

```json
{
  "content": "<@123456789012345678> Build failed!",
  "allowed_mentions": {
    "users": ["123456789012345678"]
  }
}
```

---

## 7. Multipart File Uploads

When sending files (e.g. error logs, test reports, screenshots), curl must use `multipart/form-data`:

```bash
curl -sS \
  -F "payload_json={\"content\":\"Build logs attached\",\"embeds\":[{\"title\":\"Test Run Artifacts\",\"color\":5793266}]}" \
  -F "file1=@/var/log/build.log;filename=build.log" \
  "$WEBHOOK_URL"
```

### Constraints:
- Default webhook file limit: **8 MB** (or 25 MB / 50 MB if server is Nitro boosted).
- Up to 10 files can be uploaded per message (`file1`, `file2`, etc.).

---

## 8. HTTP Status Codes & Error Handling

| HTTP Code | Meaning | Script Action |
| :--- | :--- | :--- |
| **`204 No Content`** | Success (default) | Job complete. Script exits with 0. |
| **`200 OK`** | Success (with `?wait=true`) | Job complete, output response JSON if debugging. |
| **`400 Bad Request`** | Invalid JSON syntax or payload exceeded field length constraints | Log error body to stderr. Script exits with 1. |
| **`401 Unauthorized`** | Invalid webhook token | Log error body to stderr. Verify `DISCORD_WEBHOOK_URL`. |
| **`404 Not Found`** | Webhook channel or URL does not exist | Log error body to stderr. Check webhook URL. |
| **`429 Too Many Requests`** | Rate limit encountered | Extract `retry_after` from response, sleep, and retry. |
| **`5xx Server Error`** | Discord internal API issue | Retry with exponential backoff (e.g., 1s, 2s, 4s). |

### Rate Limits:
- Standard: **30 requests per 60 seconds** per webhook.
- Burst: **5 requests per 2 seconds**.
