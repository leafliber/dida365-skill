---
name: dida365
description: Manage tasks in Dida365 (滴答清单). Use this skill when the user wants to create, view, update, complete, delete, or filter tasks in Dida365. Triggers on mentions of '滴答清单', 'Dida365', 'TickTick', '滴答', or task management requests when the user uses Dida365.
license: MIT
---

# Dida365 Task Management Skill

Manage tasks and projects in Dida365 (滴答清单) via OpenAPI.

## Quick Start

### 1. Configure Credentials

Set environment variables:

```bash
export DIDA_CLIENT_ID="your-client-id"
export DIDA_CLIENT_SECRET="your-client-secret"
```

Get credentials from [Dida365 Developer Center](https://developer.dida365.com/manage).

### 2. Authenticate

First time usage will trigger OAuth flow automatically, or run:

```bash
python scripts/dida_api.py auth
```

This opens a browser for authorization, then saves the token locally.

### 3. Use the API

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

## Priority Values

- `0` - None (default)
- `1` - Low
- `3` - Medium
- `5` - High

## Examples

### Create a Task with Due Date

```bash
python scripts/dida_api.py create-task \
  --title "Submit proposal" \
  --project-id "work-project-id" \
  --due-date "2024-03-15T18:00:00+0800" \
  --priority 3
```

### Filter High Priority Tasks

```bash
python scripts/dida_api.py filter-tasks \
  --project-ids "project1,project2" \
  --priority "3,5"
```

### Get Today's Tasks

```bash
python scripts/dida_api.py filter-tasks \
  --start-date "$(date +%Y-%m-%dT00:00:00%z)" \
  --end-date "$(date +%Y-%m-%dT23:59:59%z)"
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DIDA_CLIENT_ID` | Yes | OAuth client ID |
| `DIDA_CLIENT_SECRET` | Yes | OAuth client secret |
| `DIDA_REDIRECT_PORT` | No | Local OAuth callback port (default: 8765) |

### Config File

Token is cached at `~/.dida365/token.json` after authentication.

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 401 | Unauthorized | Re-run `auth` command |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Verify project/task ID |

## Notes

- "inbox" is a special projectId for the user's inbox
- Dates use ISO 8601 format with timezone
- API base URL: `https://api.dida365.com/open/v1/`

## Detailed Reference

See [references/api_reference.md](references/api_reference.md) for complete API documentation.