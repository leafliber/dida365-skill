# Dida365 OpenAPI Reference

Complete API reference for Dida365 (滴答清单) OpenAPI.

## Base URL

```
https://api.dida365.com/open/v1
```

## Authentication

### Step-by-Step OAuth Flow

#### Step 1: Create OAuth Application

1. Visit [Dida365 Developer Center](https://developer.dida365.com/manage)
2. Click "创建应用" (Create Application)
3. Fill in application name
4. **Important:** Set Redirect URI to:
   ```
   http://127.0.0.1:8765/callback
   ```
   - You can change the port with `DIDA_REDIRECT_PORT` environment variable
   - Make sure the redirect URI is **exactly** as configured, including protocol (`http://`)
5. Save and note your `client_id` and `client_secret`

#### Step 2: Configure Environment Variables

```bash
export DIDA_CLIENT_ID="your-client-id"
export DIDA_CLIENT_SECRET="your-client-secret"
```

Optional: Change the local callback port
```bash
export DIDA_REDIRECT_PORT="8765"  # default is 8765
```

#### Step 3: Get Authorization URL

Run the following command to print the authorization URL:

```bash
python scripts/dida_api.py auth-url
```

Or construct manually (replace `{client_id}`):

```
https://dida365.com/oauth/authorize?client_id={client_id}&redirect_uri=http://127.0.0.1:8765/callback&response_type=code&scope=tasks:read%20tasks:write
```

#### Step 4: Authorize the Application

1. Open the authorization URL in your browser
2. Log in to your Dida365 account
3. Click "允许" (Allow) to authorize
4. You will be redirected to a URL like:
   ```
   http://127.0.0.1:8765/callback?code=xxxxxxxx
   ```
   Note: The browser may show "Cannot reach this page" because there's no local server - this is expected.

5. **Copy the `code` parameter** from the URL

#### Step 5: Exchange Code for Access Token

Run the exchange command with the authorization code:

```bash
python scripts/dida_api.py exchange-code --code "YOUR_AUTH_CODE"
```

The token will be automatically saved to `~/.dida365/token.json`.

#### Step 6: Verify Authentication

```bash
python scripts/dida_api.py auth-status
```

Or test by listing projects:

```bash
python scripts/dida_api.py projects
```

### OAuth Endpoints

| Endpoint | URL |
|----------|-----|
| Authorization | `https://dida365.com/oauth/authorize` |
| Token | `https://dida365.com/oauth/token` |

### OAuth Parameters

**Authorization Request:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| client_id | Yes | Application unique ID |
| redirect_uri | Yes | Must match configured redirect URI exactly |
| response_type | Yes | Fixed as `code` |
| scope | Yes | Must be `tasks:read tasks:write` |

**Important Notes:**
- Scope `projects:read` and `projects:write` are **NOT supported**
- Only use `tasks:read tasks:write`
- The redirect URI must be pre-registered in the developer center

**Token Request:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| code | Yes | Authorization code from callback |
| grant_type | Yes | `authorization_code` |
| redirect_uri | Yes | Same as authorization request |
| scope | Yes | `tasks:read tasks:write` |

**Authorization Header:**

The token request requires Basic authentication with client credentials:

```bash
# Encode client_id:client_secret in Base64
echo -n "client_id:client_secret" | base64

# Use in Authorization header
Authorization: Basic {base64_encoded_credentials}
```

### Token Response

```json
{
  "access_token": "your-access-token",
  "token_type": "bearer",
  "expires_in": 15551999,
  "scope": "tasks:read tasks:write"
}
```

### Token Storage

Tokens are stored in `~/.dida365/token.json`:

```json
{
  "access_token": "...",
  "expires_in": 15551999,
  "token_type": "bearer",
  "created_at": 1773754134.555,
  "client_id": "your-client-id"
}
```

File permissions are set to `600` (owner read/write only) for security.

### Token Expiry

- Tokens are valid for approximately **179 days** (about 6 months)
- The skill automatically handles token refresh if a refresh token is available
- If you get a 401 error, re-run the authorization flow

---

## Task API

### Get Task

```http
GET /project/{projectId}/task/{taskId}
```

**Response:**
```json
{
  "id": "63b7bebb91c0a5474805fcd4",
  "projectId": "6226ff9877acee87727f6bca",
  "title": "Task Title",
  "content": "Task Content",
  "desc": "Task Description",
  "isAllDay": true,
  "startDate": "2019-11-13T03:00:00+0000",
  "dueDate": "2019-11-14T03:00:00+0000",
  "timeZone": "America/Los_Angeles",
  "reminders": ["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"],
  "repeatFlag": "RRULE:FREQ=DAILY;INTERVAL=1",
  "priority": 1,
  "status": 0,
  "completedTime": null,
  "sortOrder": 12345,
  "items": [],
  "kind": "TEXT"
}
```

### Create Task

```http
POST /task
```

**Request Body:**
```json
{
  "title": "Task Title",
  "projectId": "6226ff9877acee87727f6bca",
  "content": "Task content",
  "desc": "Description",
  "isAllDay": true,
  "startDate": "2019-11-13T03:00:00+0000",
  "dueDate": "2019-11-14T03:00:00+0000",
  "timeZone": "Asia/Shanghai",
  "reminders": ["TRIGGER:P0DT9H0M0S"],
  "repeatFlag": "RRULE:FREQ=DAILY;INTERVAL=1",
  "priority": 1,
  "items": [
    {
      "title": "Subtask title",
      "status": 0
    }
  ]
}
```

**Required Fields:**
- `title` - Task title
- `projectId` - Project ID (use "inbox" for inbox)

### Update Task

```http
POST /task/{taskId}
```

**Request Body:**
```json
{
  "id": "task-id",
  "projectId": "project-id",
  "title": "Updated Title",
  "priority": 3
}
```

**Required Fields:**
- `id` - Task ID
- `projectId` - Project ID

### Complete Task

```http
POST /project/{projectId}/task/{taskId}/complete
```

### Uncomplete Task

```http
POST /project/{projectId}/task/{taskId}/uncomplete
```

### Delete Task

```http
DELETE /project/{projectId}/task/{taskId}
```

### Move Task

```http
POST /task/move
```

**Request Body:**
```json
[
  {
    "fromProjectId": "source-project-id",
    "toProjectId": "target-project-id",
    "taskId": "task-id"
  }
]
```

### Filter Tasks

```http
POST /task/filter
```

**Request Body:**
```json
{
  "projectIds": ["project-id-1", "project-id-2"],
  "startDate": "2024-03-01T00:00:00.000+0000",
  "endDate": "2024-03-31T23:59:59.000+0000",
  "priority": [0, 1],
  "tag": ["urgent", "work"],
  "status": [0]
}
```

### List Completed Tasks

```http
POST /task/completed
```

**Request Body:**
```json
{
  "projectIds": ["project-id"],
  "startDate": "2024-03-01T00:00:00.000+0000",
  "endDate": "2024-03-31T23:59:59.000+0000",
  "limit": 50
}
```

---

## Project API

### Get All Projects

```http
GET /project
```

**Response:**
```json
[
  {
    "id": "6226ff9877acee87727f6bca",
    "name": "Project Name",
    "color": "#F18181",
    "closed": false,
    "groupId": "6436176a47fd2e05f26ef56e",
    "viewMode": "list",
    "permission": "write",
    "kind": "TASK"
  }
]
```

### Get Project by ID

```http
GET /project/{projectId}
```

### Get Project with Tasks

```http
GET /project/{projectId}/data
```

**Response:**
```json
{
  "project": {
    "id": "project-id",
    "name": "Project Name",
    "color": "#F18181"
  },
  "tasks": [...],
  "columns": [...]
}
```

**Note:** Use `"inbox"` as projectId to get inbox data.

### Create Project

```http
POST /project
```

**Request Body:**
```json
{
  "name": "New Project",
  "color": "#F18181",
  "viewMode": "list",
  "kind": "TASK"
}
```

### Update Project

```http
POST /project/{projectId}
```

### Delete Project

```http
DELETE /project/{projectId}
```

---

## Data Models

### Task

| Field | Type | Description |
|-------|------|-------------|
| id | string | Task identifier |
| projectId | string | Project ID |
| title | string | Task title |
| content | string | Task content/notes |
| desc | string | Description for checklist |
| isAllDay | boolean | All-day task |
| startDate | datetime | Start date (`yyyy-MM-dd'T'HH:mm:ssZ`) |
| dueDate | datetime | Due date |
| timeZone | string | Time zone (e.g., "Asia/Shanghai") |
| reminders | array | List of reminder triggers |
| repeatFlag | string | RRULE for recurring tasks |
| priority | integer | 0=None, 1=Low, 3=Medium, 5=High |
| status | integer | 0=Normal, 2=Completed |
| completedTime | datetime | Completion time |
| sortOrder | integer | Sort order |
| items | array | Subtasks/checklist items |
| kind | string | "TEXT", "NOTE", "CHECKLIST" |

### ChecklistItem (Subtask)

| Field | Type | Description |
|-------|------|-------------|
| id | string | Subtask ID |
| title | string | Subtask title |
| status | integer | 0=Normal, 1=Completed |
| completedTime | datetime | Completion time |
| isAllDay | boolean | All-day |
| sortOrder | integer | Sort order |
| startDate | datetime | Start date |
| timeZone | string | Time zone |

### Project

| Field | Type | Description |
|-------|------|-------------|
| id | string | Project identifier |
| name | string | Project name |
| color | string | Color (e.g., "#F18181") |
| sortOrder | integer | Sort order |
| closed | boolean | Is closed |
| groupId | string | Project group ID |
| viewMode | string | "list", "kanban", "timeline" |
| permission | string | "read", "write", "comment" |
| kind | string | "TASK" or "NOTE" |

---

## Priority Values

| Value | Meaning |
|-------|---------|
| 0 | None (default) |
| 1 | Low |
| 3 | Medium |
| 5 | High |

## Status Values

| Value | Meaning |
|-------|---------|
| 0 | Normal (incomplete) |
| 2 | Completed |

---

## Date Format

All dates use ISO 8601 format with timezone:

```
yyyy-MM-dd'T'HH:mm:ssZ
```

Example: `2019-11-13T03:00:00+0000`

---

## Error Responses

| HTTP Code | Description | Action |
|-----------|-------------|--------|
| 200 | OK | Success |
| 201 | Created | Success |
| 204 | No Content | Success (no response body) |
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Re-authenticate |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Verify ID exists |

---

## Rate Limits

Refer to Dida365 documentation for current rate limits.

---

## Support

For questions or feedback, contact: support@dida365.com