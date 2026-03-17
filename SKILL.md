---
name: dida365
description: Manage tasks in Dida365 (滴答清单). Use this skill when the user wants to create, view, update, complete, delete, or filter tasks in Dida365. Also handles project operations. Triggers on mentions of '滴答清单', 'Dida365', 'TickTick', '滴答', or task management requests when the user uses Dida365.
license: MIT
---

# Dida365 Task Management Skill

Manage tasks and projects in Dida365 (滴答清单) via OpenAPI.

## Prerequisites

Before using this skill, the user must have:

1. **Dida365 account** - Registered at dida365.com
2. **OAuth credentials** - Obtained from [Dida365 Developer Center](https://developer.dida365.com/manage)
   - `client_id`
   - `client_secret`
3. **Access token** - Obtained via OAuth2 flow

### Configuration

Store credentials in environment variables or a config file:

```bash
export DIDA_ACCESS_TOKEN="your-access-token"
```

Or create a config file at `~/.dida365/config.json`:

```json
{
  "access_token": "your-access-token"
}
```

## Quick Reference

### Task Operations

| Action | Command |
|--------|---------|
| List projects | `dida_api.py projects` |
| Get project tasks | `dida_api.py project-data <projectId>` |
| Create task | `dida_api.py create-task --title "..." --project-id <id>` |
| Get task | `dida_api.py get-task <projectId> <taskId>` |
| Update task | `dida_api.py update-task <taskId> --title "..."` |
| Complete task | `dida_api.py complete-task <projectId> <taskId>` |
| Delete task | `dida_api.py delete-task <projectId> <taskId>` |
| Filter tasks | `dida_api.py filter-tasks --project-ids <id1,id2>` |
| Completed tasks | `dida_api.py completed-tasks --project-ids <id1,id2>` |
| Move task | `dida_api.py move-task <taskId> <fromProjectId> <toProjectId>` |

### Project Operations

| Action | Command |
|--------|---------|
| List all projects | `dida_api.py projects` |
| Get project info | `dida_api.py project <projectId>` |
| Create project | `dida_api.py create-project --name "..."` |
| Delete project | `dida_api.py delete-project <projectId>` |

## Task Properties

| Field | Type | Description |
|-------|------|-------------|
| title | string | Task title (required for creation) |
| projectId | string | Project ID (required) |
| content | string | Task content/notes |
| desc | string | Description for checklist items |
| startDate | datetime | Start date (format: `yyyy-MM-dd'T'HH:mm:ssZ`) |
| dueDate | datetime | Due date |
| priority | int | 0=None, 1=Low, 3=Medium, 5=High |
| isAllDay | bool | All-day task |
| timeZone | string | e.g., "Asia/Shanghai" |
| reminders | list | Reminder triggers |
| repeatFlag | string | RRULE format for recurring tasks |
| items | list | Subtasks/checklist items |

## Priority Values

- `0` - None (default)
- `1` - Low
- `3` - Medium
- `5` - High

## Task Status

- `0` - Normal (incomplete)
- `2` - Completed

## Common Workflows

### Create a Simple Task

```bash
python scripts/dida_api.py create-task \
  --title "Review quarterly report" \
  --project-id "inbox"
```

### Create Task with Due Date and Priority

```bash
python scripts/dida_api.py create-task \
  --title "Submit proposal" \
  --project-id "work-project-id" \
  --due-date "2024-03-15T18:00:00+0800" \
  --priority 3
```

### Filter Tasks by Tags

```bash
python scripts/dida_api.py filter-tasks \
  --project-ids "project1,project2" \
  --tags "urgent,work"
```

### Get Today's Tasks

1. List all projects to get project IDs
2. Filter tasks with date range for today

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `201` - Created
- `401` - Unauthorized (check access token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (invalid ID)

## OAuth2 Flow

If the user needs to obtain an access token:

1. Direct user to authorization URL:
   ```
   https://dida365.com/oauth/authorize?scope=tasks:read%20tasks:write&client_id=YOUR_CLIENT_ID&state=random_state&redirect_uri=YOUR_REDIRECT_URI&response_type=code
   ```

2. User grants access, receives callback with `code`

3. Exchange code for token:
   ```bash
   curl -X POST https://dida365.com/oauth/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -u "client_id:client_secret" \
     -d "code=AUTH_CODE&grant_type=authorization_code&scope=tasks:read tasks:write&redirect_uri=YOUR_REDIRECT_URI"
   ```

4. Store the `access_token` from response

## Notes

- "inbox" is a special projectId representing the user's inbox
- All dates use ISO 8601 format with timezone
- The API base URL is `https://api.dida365.com/open/v1/`
- For detailed API reference, see `references/api_reference.md`