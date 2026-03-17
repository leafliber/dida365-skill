# Dida365 Skill

Agent Skill for managing tasks in Dida365 (滴答清单) via OpenAPI.

## Features

- **Simple OAuth Flow**: Easy authorization with manual code exchange
- **Full Task Management**: Create, read, update, complete, delete, and filter tasks
- **Project Operations**: List, create, and manage projects
- **Advanced Filtering**: Filter tasks by date, priority, tags, and status

## Quick Start

### 1. Create OAuth Application

1. Visit [Dida365 Developer Center](https://developer.dida365.com/manage)
2. Click "创建应用" (Create Application)
3. Fill in application name
4. **Important:** Set Redirect URI to:
   ```
   http://127.0.0.1:8765/callback
   ```
5. Save and note your `client_id` and `client_secret`

### 2. Configure Environment

```bash
export DIDA_CLIENT_ID="your-client-id"
export DIDA_CLIENT_SECRET="your-client-secret"
```

### 3. Get Authorization URL

```bash
python scripts/dida_api.py auth-url
```

Open the printed URL in your browser.

### 4. Authorize and Get Code

1. Log in to your Dida365 account
2. Click "允许" (Allow) to authorize
3. You'll be redirected to a URL like:
   ```
   http://127.0.0.1:8765/callback?code=xxxxxxxx
   ```
4. Copy the `code` parameter

### 5. Exchange Code for Token

```bash
python scripts/dida_api.py exchange-code --code "YOUR_CODE"
```

### 6. Verify and Use

```bash
# Check authentication
python scripts/dida_api.py auth-status

# List projects
python scripts/dida_api.py projects

# Create a task
python scripts/dida_api.py create-task --title "My task" --project-id "inbox"
```

## Commands Reference

### Authentication

| Command | Description |
|---------|-------------|
| `auth-url` | Print the authorization URL |
| `exchange-code --code CODE` | Exchange authorization code for token |
| `auth-status` | Check authentication status |
| `logout` | Clear saved credentials |

### Projects

| Command | Description |
|---------|-------------|
| `projects` | List all projects |
| `project <id>` | Get project info |
| `project-data <id>` | Get project with tasks |

### Tasks

| Command | Description |
|---------|-------------|
| `create-task --title "..." --project-id <id>` | Create a task |
| `get-task <projectId> <taskId>` | Get task details |
| `update-task <taskId> --project-id <id> [options]` | Update a task |
| `complete-task <projectId> <taskId>` | Mark task complete |
| `delete-task <projectId> <taskId>` | Delete a task |
| `filter-tasks [options]` | Filter tasks |
| `completed-tasks [options]` | List completed tasks |

## Task Options

| Option | Description |
|--------|-------------|
| `--title` | Task title |
| `--project-id` | Project ID (use "inbox" for inbox) |
| `--content` | Task content/notes |
| `--due-date` | Due date (format: `YYYY-MM-DDTHH:mm:ss+ZZZZ`) |
| `--priority` | 0=None, 1=Low, 3=Medium, 5=High |
| `--tags` | Comma-separated tags |

## Important Notes

### OAuth Scope

**Only these scopes are supported:**
- `tasks:read`
- `tasks:write`

**NOT supported:**
- `projects:read`
- `projects:write`

### Redirect URI

The redirect URI must be **pre-registered** in the Dida365 Developer Center. Make sure it matches exactly:
- `http://127.0.0.1:8765/callback` (not `localhost`)

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DIDA_CLIENT_ID` | Yes | OAuth client ID |
| `DIDA_CLIENT_SECRET` | Yes | OAuth client secret |
| `DIDA_REDIRECT_PORT` | No | Local callback port (default: 8765) |

### Token Storage

Tokens are stored in `~/.dida365/token.json` with file permissions 600.

Token validity: approximately **179 days** (6 months).

## Examples

### Create a Task

```bash
python scripts/dida_api.py create-task \
  --title "Submit report" \
  --project-id "inbox" \
  --due-date "2024-03-15T18:00:00+0800" \
  --priority 3 \
  --tags "work,urgent"
```

### Filter Today's Tasks

```bash
python scripts/dida_api.py filter-tasks \
  --start-date "$(date +%Y-%m-%dT00:00:00%z)" \
  --end-date "$(date +%Y-%m-%dT23:59:59%z)"
```

### Get Inbox Tasks

```bash
python scripts/dida_api.py project-data inbox
```

## API Reference

See [references/api_reference.md](references/api_reference.md) for complete API documentation.

## Troubleshooting

### "At least one redirect_uri must be registered"

Register the redirect URI in the Dida365 Developer Center:
- URL: `http://127.0.0.1:8765/callback`

### "Invalid scope"

Only use `tasks:read tasks:write`. Other scopes are not supported.

### 401 Unauthorized

Your token may have expired. Re-run the authorization flow:
1. `python scripts/dida_api.py auth-url`
2. Open URL, authorize, get code
3. `python scripts/dida_api.py exchange-code --code "YOUR_CODE"`

## License

MIT License