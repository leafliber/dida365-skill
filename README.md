# Dida365 Skill

Agent Skill for managing tasks in Dida365 (滴答清单) via OpenAPI with automatic OAuth authentication.

## Features

- **Automatic OAuth Flow**: Just set client credentials, authentication is handled automatically
- **Token Management**: Automatic token refresh and secure local storage
- **Full Task Management**: Create, read, update, complete, delete, and filter tasks
- **Project Operations**: List, create, and manage projects
- **Advanced Filtering**: Filter tasks by date, priority, tags, and status

## Quick Start

### 1. Get OAuth Credentials

1. Visit [Dida365 Developer Center](https://developer.dida365.com/manage)
2. Create a new application
3. Set redirect URI to: `http://127.0.0.1:8765/callback`
4. Note your `client_id` and `client_secret`

### 2. Configure Environment

```bash
export DIDA_CLIENT_ID="your-client-id"
export DIDA_CLIENT_SECRET="your-client-secret"
```

### 3. Authenticate

```bash
python scripts/dida_api.py auth
```

This opens a browser for authorization, then saves the token locally.

### 4. Use the API

```bash
# List projects
python scripts/dida_api.py projects

# Create task
python scripts/dida_api.py create-task --title "Review report" --project-id "inbox"

# Complete task
python scripts/dida_api.py complete-task <projectId> <taskId>
```

## Commands Reference

### Authentication

| Command | Description |
|---------|-------------|
| `auth` | Run OAuth flow to get access token |
| `auth-status` | Check authentication status |
| `logout` | Clear saved credentials |

### Projects

| Command | Description |
|---------|-------------|
| `projects` | List all projects |
| `project <id>` | Get project info |
| `project-data <id>` | Get project with tasks |
| `create-project --name "..."` | Create a project |
| `delete-project <id>` | Delete a project |

### Tasks

| Command | Description |
|---------|-------------|
| `create-task --title "..." --project-id <id>` | Create a task |
| `get-task <projectId> <taskId>` | Get task details |
| `update-task <taskId> --project-id <id> [options]` | Update a task |
| `complete-task <projectId> <taskId>` | Mark task complete |
| `uncomplete-task <projectId> <taskId>` | Mark task incomplete |
| `delete-task <projectId> <taskId>` | Delete a task |
| `move-task <taskId> <fromProjectId> <toProjectId>` | Move task |
| `filter-tasks [options]` | Filter tasks |
| `completed-tasks [options]` | List completed tasks |

## Task Options

| Option | Description |
|--------|-------------|
| `--title` | Task title |
| `--project-id` | Project ID (required, use "inbox" for inbox) |
| `--content` | Task content/notes |
| `--due-date` | Due date (format: `YYYY-MM-DDTHH:mm:ss+ZZZZ`) |
| `--start-date` | Start date |
| `--priority` | 0=None, 1=Low, 3=Medium, 5=High |
| `--is-all-day` | All-day task |
| `--time-zone` | Time zone (e.g., Asia/Shanghai) |
| `--tags` | Comma-separated tags |

## Filter Options

| Option | Description |
|--------|-------------|
| `--project-ids` | Comma-separated project IDs |
| `--start-date` | Filter start date |
| `--end-date` | Filter end date |
| `--priority` | Comma-separated priorities (0,1,3,5) |
| `--tags` | Comma-separated tags |
| `--status` | Comma-separated status (0=open, 2=completed) |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DIDA_CLIENT_ID` | Yes | OAuth client ID |
| `DIDA_CLIENT_SECRET` | Yes | OAuth client secret |
| `DIDA_REDIRECT_PORT` | No | Local OAuth callback port (default: 8765) |

### Token Storage

Tokens are securely stored in `~/.dida365/token.json` with file permissions 600.

## Examples

### Create a High-Priority Task

```bash
python scripts/dida_api.py create-task \
  --title "Submit proposal" \
  --project-id "work-project-id" \
  --due-date "2024-03-15T18:00:00+0800" \
  --priority 5 \
  --tags "urgent,work"
```

### Filter Today's High-Priority Tasks

```bash
python scripts/dida_api.py filter-tasks \
  --start-date "$(date +%Y-%m-%dT00:00:00%z)" \
  --end-date "$(date +%Y-%m-%dT23:59:59%z)" \
  --priority "3,5"
```

### Get Inbox Tasks

```bash
python scripts/dida_api.py project-data inbox
```

## API Reference

See [references/api_reference.md](references/api_reference.md) for complete API documentation.

## License

MIT License