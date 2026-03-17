# Dida365 Skill

Agent Skill for managing tasks in Dida365 (滴答清单) via OpenAPI.

## Features

- **Full Task Management**: Create, read, update, complete, delete, and move tasks
- **Project Operations**: List, create, and manage projects
- **Advanced Filtering**: Filter tasks by date, priority, tags, and status
- **OAuth2 Support**: Secure authentication flow

## Installation

1. Clone or download this skill to your skills directory
2. Install dependencies (Python 3.x required)

## Configuration

### Option 1: Environment Variable

```bash
export DIDA_ACCESS_TOKEN="your-access-token"
```

### Option 2: Config File

Create `~/.dida365/config.json`:

```json
{
  "access_token": "your-access-token"
}
```

## Getting Access Token

### Step 1: Register Application

1. Go to [Dida365 Developer Center](https://developer.dida365.com/manage)
2. Create a new application
3. Note your `client_id` and `client_secret`
4. Configure your redirect URI

### Step 2: Authorize

```bash
python scripts/dida_api.py oauth-url \
  --client-id YOUR_CLIENT_ID \
  --redirect-uri YOUR_REDIRECT_URI
```

Visit the generated URL and authorize the application.

### Step 3: Exchange Code

```bash
python scripts/dida_api.py oauth-token \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --code AUTHORIZATION_CODE \
  --redirect-uri YOUR_REDIRECT_URI \
  --save
```

## Usage

### List Projects

```bash
python scripts/dida_api.py projects
```

### Create Task

```bash
python scripts/dida_api.py create-task \
  --title "Review quarterly report" \
  --project-id "inbox"
```

### Complete Task

```bash
python scripts/dida_api.py complete-task PROJECT_ID TASK_ID
```

### Filter Tasks

```bash
python scripts/dida_api.py filter-tasks \
  --project-ids "project1,project2" \
  --priority "3,5" \
  --tags "urgent"
```

## API Reference

See [references/api_reference.md](references/api_reference.md) for complete API documentation.

## License

MIT License