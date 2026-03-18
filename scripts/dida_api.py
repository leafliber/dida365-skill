#!/usr/bin/env python3
"""
Dida365 (滴答清单) OpenAPI Client

Automatic OAuth flow - just set DIDA_CLIENT_ID and DIDA_CLIENT_SECRET.

Usage:
    python dida_api.py auth              # Run OAuth flow
    python dida_api.py auth-status       # Check authentication
    python dida_api.py logout            # Clear credentials

    python dida_api.py projects          # List projects
    python dida_api.py create-task ...   # Create task
    ...

Environment Variables:
    DIDA_CLIENT_ID       - OAuth client ID (required)
    DIDA_CLIENT_SECRET   - OAuth client secret (required)
    DIDA_REDIRECT_PORT   - Local callback port (default: 8765)
"""

import argparse
import json
import os
import sys
import time
import webbrowser
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse
import urllib.request
import urllib.error
import base64
import hashlib
import secrets

# API Configuration
API_BASE_URL = "https://api.dida365.com/open/v1"
OAUTH_BASE_URL = "https://dida365.com/oauth"

# Token 存储路径 - 优先使用环境变量，默认使用 working 目录
# 这样 token 会保存在持久化的 working 目录中，不会因容器重启丢失
DIDA_CONFIG_DIR = os.environ.get("DIDA_CONFIG_DIR", "/app/working/.dida365")
CONFIG_DIR = Path(DIDA_CONFIG_DIR)
TOKEN_FILE = CONFIG_DIR / "token.json"

# OAuth Configuration
DEFAULT_REDIRECT_PORT = 8765
OAUTH_SCOPE = "tasks:read tasks:write projects:read projects:write"


def get_client_credentials() -> tuple[str, str]:
    """Get OAuth client credentials from environment."""
    client_id = os.environ.get("DIDA_CLIENT_ID")
    client_secret = os.environ.get("DIDA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "OAuth credentials not found. Please set:\n"
            "  export DIDA_CLIENT_ID='your-client-id'\n"
            "  export DIDA_CLIENT_SECRET='your-client-secret'\n\n"
            "Get credentials from: https://developer.dida365.com/manage"
        )

    return client_id, client_secret


def get_redirect_port() -> int:
    """Get OAuth redirect port from environment."""
    return int(os.environ.get("DIDA_REDIRECT_PORT", DEFAULT_REDIRECT_PORT))


def load_token() -> Optional[dict]:
    """Load token from file."""
    if not TOKEN_FILE.exists():
        return None

    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_token(token_data: dict, client_id: str):
    """Save token to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    token_info = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
        "token_type": token_data.get("token_type", "Bearer"),
        "created_at": time.time(),
        "client_id": client_id,
    }

    with open(TOKEN_FILE, "w") as f:
        json.dump(token_info, f, indent=2)

    # Set restrictive permissions
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass


def is_token_expired(token_info: dict) -> bool:
    """Check if token is expired or about to expire."""
    if not token_info:
        return True

    created_at = token_info.get("created_at", 0)
    expires_in = token_info.get("expires_in", 3600)

    # Consider expired if within 5 minutes of expiry
    return time.time() > (created_at + expires_in - 300)


def get_valid_token() -> str:
    """Get a valid access token, refreshing or authenticating if needed."""
    client_id, client_secret = get_client_credentials()

    token_info = load_token()

    # No token or wrong client - need to authenticate
    if not token_info or token_info.get("client_id") != client_id:
        print("No valid token found. Starting OAuth flow...")
        return run_oauth_flow(client_id, client_secret)

    # Token expired - try to refresh
    if is_token_expired(token_info):
        print("Token expired. Refreshing...")
        refresh_token = token_info.get("refresh_token")

        if refresh_token:
            try:
                new_token = refresh_access_token(client_id, client_secret, refresh_token)
                save_token(new_token, client_id)
                return new_token["access_token"]
            except Exception as e:
                print(f"Token refresh failed: {e}")
                print("Starting new OAuth flow...")
                return run_oauth_flow(client_id, client_secret)
        else:
            print("No refresh token. Starting OAuth flow...")
            return run_oauth_flow(client_id, client_secret)

    return token_info["access_token"]


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Refresh the access token using refresh token."""
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    body = urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })

    req = urllib.request.Request(
        f"{OAUTH_BASE_URL}/token",
        data=body.encode(),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        """Handle OAuth callback."""
        parsed = urlparse(self.path)

        if parsed.path != "/callback":
            self.send_error(404)
            return

        query = parse_qs(parsed.query)

        if "error" in query:
            self.error = query["error"][0]
            error_desc = query.get("error_description", ["Unknown error"])[0]
            self._send_response(f"Authentication failed: {error_desc}", success=False)
            return

        if "code" in query:
            OAuthCallbackHandler.auth_code = query["code"][0]
            self._send_response("Authentication successful! You can close this window.")
            return

        self.send_error(400, "Missing authorization code")

    def _send_response(self, message: str, success: bool = True):
        """Send HTML response."""
        self.send_response(200 if success else 400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dida365 Authentication</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: {'#f0f9ff' if success else '#fef2f2'};
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 16px;
                }}
                h1 {{ color: {'#0369a1' if success else '#dc2626'}; margin-bottom: 8px; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">{'✅' if success else '❌'}</div>
                <h1>{'Authentication Successful!' if success else 'Authentication Failed'}</h1>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_oauth_flow(client_id: str, client_secret: str) -> str:
    """Run the complete OAuth flow."""
    port = get_redirect_port()
    redirect_uri = f"http://127.0.0.1:{port}/callback"

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(16)

    # Build authorization URL
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": OAUTH_SCOPE,
        "state": state,
    }
    auth_url = f"{OAUTH_BASE_URL}/authorize?{urlencode(auth_params)}"

    print(f"\n{'='*60}")
    print("Dida365 OAuth Authentication")
    print(f"{'='*60}")
    print(f"\nOpening browser for authorization...")
    print(f"If the browser doesn't open automatically, visit:\n{auth_url}\n")

    # Start local server
    server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
    server.timeout = 120  # 2 minute timeout

    # Open browser
    webbrowser.open(auth_url)

    # Wait for callback
    print(f"Waiting for authorization (listening on port {port})...")

    try:
        while OAuthCallbackHandler.auth_code is None and OAuthCallbackHandler.error is None:
            server.handle_request()
    except KeyboardInterrupt:
        print("\nAuthentication cancelled.")
        sys.exit(1)

    server.server_close()

    if OAuthCallbackHandler.error:
        raise Exception(f"OAuth error: {OAuthCallbackHandler.error}")

    auth_code = OAuthCallbackHandler.auth_code

    # Exchange code for token
    print("Exchanging authorization code for token...")

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    body = urlencode({
        "code": auth_code,
        "grant_type": "authorization_code",
        "scope": OAUTH_SCOPE,
        "redirect_uri": redirect_uri,
    })

    req = urllib.request.Request(
        f"{OAUTH_BASE_URL}/token",
        data=body.encode(),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as response:
            token_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"Token exchange failed: {error_body}")

    # Save token
    save_token(token_data, client_id)
    print(f"\n✅ Token saved to: {TOKEN_FILE}")

    return token_data["access_token"]


def api_request(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> Any:
    """Make an API request to Dida365."""
    token = get_valid_token()

    url = f"{API_BASE_URL}{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    body = None
    if data:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                return {"success": True}
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            error_body = e.read().decode("utf-8") if e.fp else ""
            print(f"Authentication error. Token may be invalid or expired.")
            print("Try running: python dida_api.py auth")
            raise Exception(f"Authentication error (401): {error_body}")

        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"API Error {e.code}: {error_body}")


def format_output(data: Any) -> str:
    """Format output for display."""
    return json.dumps(data, indent=2, ensure_ascii=False)


# ============================================================================
# Authentication Commands
# ============================================================================


def cmd_auth(args):
    """Run OAuth authentication flow."""
    client_id, client_secret = get_client_credentials()
    token = run_oauth_flow(client_id, client_secret)
    print("\n✅ Authentication successful!")
    print("You can now use the API.")


def cmd_auth_status(args):
    """Check authentication status."""
    try:
        client_id, client_secret = get_client_credentials()
        print(f"Client ID: {client_id[:8]}...")
    except ValueError as e:
        print(f"❌ {e}")
        return

    token_info = load_token()

    if not token_info:
        print("❌ No token found. Run 'auth' to authenticate.")
        return

    print(f"\nToken file: {TOKEN_FILE}")

    if token_info.get("client_id") != client_id:
        print("⚠️  Token was created with a different client ID.")
        return

    created_at = token_info.get("created_at", 0)
    expires_in = token_info.get("expires_in", 3600)
    expires_at = created_at + expires_in
    remaining = expires_at - time.time()

    if remaining <= 0:
        print("❌ Token has expired.")
        print("   Run 'auth' to re-authenticate, or the API will auto-refresh.")
    elif remaining < 300:
        print(f"⚠️  Token expires in {int(remaining)} seconds.")
        print("   Will auto-refresh on next API call.")
    else:
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        print(f"✅ Token valid for {hours}h {minutes}m")

    print(f"   Token type: {token_info.get('token_type', 'Bearer')}")
    print(f"   Has refresh token: {'Yes' if token_info.get('refresh_token') else 'No'}")


def cmd_logout(args):
    """Clear saved credentials."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print(f"✅ Token file deleted: {TOKEN_FILE}")
    else:
        print("No token file to delete.")


# ============================================================================
# Project Commands
# ============================================================================


def cmd_projects(args):
    """List all projects."""
    result = api_request("GET", "/project")
    print(format_output(result))


def cmd_project(args):
    """Get project info."""
    result = api_request("GET", f"/project/{args.projectId}")
    print(format_output(result))


def cmd_project_data(args):
    """Get project with tasks."""
    result = api_request("GET", f"/project/{args.projectId}/data")
    print(format_output(result))


def cmd_create_project(args):
    """Create a new project."""
    data = {"name": args.name}
    if args.color:
        data["color"] = args.color
    if args.view_mode:
        data["viewMode"] = args.view_mode
    if args.kind:
        data["kind"] = args.kind

    result = api_request("POST", "/project", data=data)
    print(format_output(result))


def cmd_delete_project(args):
    """Delete a project."""
    result = api_request("DELETE", f"/project/{args.projectId}")
    print(format_output({"success": True, "message": f"Project {args.projectId} deleted"}))


# ============================================================================
# Task Commands
# ============================================================================


def cmd_create_task(args):
    """Create a new task."""
    data = {
        "title": args.title,
        "projectId": args.project_id,
    }

    if args.content:
        data["content"] = args.content
    if args.due_date:
        data["dueDate"] = args.due_date
    if args.start_date:
        data["startDate"] = args.start_date
    if args.priority is not None:
        data["priority"] = args.priority
    if args.is_all_day:
        data["isAllDay"] = True
    if args.time_zone:
        data["timeZone"] = args.time_zone
    if args.tags:
        data["tags"] = [t.strip() for t in args.tags.split(",")]

    result = api_request("POST", "/task", data=data)
    print(format_output(result))


def cmd_get_task(args):
    """Get task details."""
    result = api_request("GET", f"/project/{args.projectId}/task/{args.taskId}")
    print(format_output(result))


def cmd_update_task(args):
    """Update a task."""
    data = {"id": args.taskId, "projectId": args.project_id}

    if args.title:
        data["title"] = args.title
    if args.content:
        data["content"] = args.content
    if args.due_date:
        data["dueDate"] = args.due_date
    if args.start_date:
        data["startDate"] = args.start_date
    if args.priority is not None:
        data["priority"] = args.priority
    if args.is_all_day is not None:
        data["isAllDay"] = args.is_all_day
    if args.tags:
        data["tags"] = [t.strip() for t in args.tags.split(",")]

    result = api_request("POST", f"/task/{args.taskId}", data=data)
    print(format_output(result))


def cmd_complete_task(args):
    """Mark task as complete."""
    result = api_request("POST", f"/project/{args.projectId}/task/{args.taskId}/complete")
    print(format_output({"success": True, "message": f"Task {args.taskId} completed"}))


def cmd_uncomplete_task(args):
    """Mark task as incomplete."""
    result = api_request("POST", f"/project/{args.projectId}/task/{args.taskId}/uncomplete")
    print(format_output({"success": True, "message": f"Task {args.taskId} uncompleted"}))


def cmd_delete_task(args):
    """Delete a task."""
    result = api_request("DELETE", f"/project/{args.projectId}/task/{args.taskId}")
    print(format_output({"success": True, "message": f"Task {args.taskId} deleted"}))


def cmd_move_task(args):
    """Move task to another project."""
    data = [
        {
            "taskId": args.taskId,
            "fromProjectId": args.fromProjectId,
            "toProjectId": args.toProjectId,
        }
    ]
    result = api_request("POST", "/task/move", data=data)
    print(format_output(result))


def cmd_filter_tasks(args):
    """Filter tasks with criteria."""
    data = {}

    if args.project_ids:
        data["projectIds"] = [p.strip() for p in args.project_ids.split(",")]
    if args.start_date:
        data["startDate"] = args.start_date
    if args.end_date:
        data["endDate"] = args.end_date
    if args.priority:
        data["priority"] = [int(p.strip()) for p in args.priority.split(",")]
    if args.tags:
        data["tag"] = [t.strip() for t in args.tags.split(",")]
    if args.status:
        data["status"] = [int(s.strip()) for s in args.status.split(",")]
    if args.is_all_day is not None:
        data["isAllDay"] = args.is_all_day

    result = api_request("POST", "/task/filter", data=data)
    print(format_output(result))


def cmd_completed_tasks(args):
    """List completed tasks."""
    data = {}

    if args.project_ids:
        data["projectIds"] = [p.strip() for p in args.project_ids.split(",")]
    if args.start_date:
        data["startDate"] = args.start_date
    if args.end_date:
        data["endDate"] = args.end_date
    if args.limit:
        data["limit"] = args.limit

    result = api_request("POST", "/task/completed", data=data)
    print(format_output(result))


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Dida365 (滴答清单) API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Authentication commands
    auth_parser = subparsers.add_parser("auth", help="Run OAuth authentication")
    auth_parser.set_defaults(func=cmd_auth)

    auth_status_parser = subparsers.add_parser("auth-status", help="Check authentication status")
    auth_status_parser.set_defaults(func=cmd_auth_status)

    logout_parser = subparsers.add_parser("logout", help="Clear saved credentials")
    logout_parser.set_defaults(func=cmd_logout)

    # Project commands
    proj_list = subparsers.add_parser("projects", help="List all projects")
    proj_list.set_defaults(func=cmd_projects)

    proj_get = subparsers.add_parser("project", help="Get project info")
    proj_get.add_argument("projectId", help="Project ID")
    proj_get.set_defaults(func=cmd_project)

    proj_data = subparsers.add_parser("project-data", help="Get project with tasks")
    proj_data.add_argument("projectId", help="Project ID (use 'inbox' for inbox)")
    proj_data.set_defaults(func=cmd_project_data)

    proj_create = subparsers.add_parser("create-project", help="Create a new project")
    proj_create.add_argument("--name", required=True, help="Project name")
    proj_create.add_argument("--color", help="Project color (e.g., #F18181)")
    proj_create.add_argument("--view-mode", choices=["list", "kanban", "timeline"])
    proj_create.add_argument("--kind", choices=["TASK", "NOTE"])
    proj_create.set_defaults(func=cmd_create_project)

    proj_delete = subparsers.add_parser("delete-project", help="Delete a project")
    proj_delete.add_argument("projectId", help="Project ID")
    proj_delete.set_defaults(func=cmd_delete_project)

    # Task commands
    task_create = subparsers.add_parser("create-task", help="Create a new task")
    task_create.add_argument("--title", required=True, help="Task title")
    task_create.add_argument("--project-id", required=True, help="Project ID (use 'inbox' for inbox)")
    task_create.add_argument("--content", help="Task content")
    task_create.add_argument("--due-date", help="Due date (format: YYYY-MM-DDTHH:mm:ss+ZZZZ)")
    task_create.add_argument("--start-date", help="Start date")
    task_create.add_argument("--priority", type=int, choices=[0, 1, 3, 5], help="Priority: 0=None, 1=Low, 3=Medium, 5=High")
    task_create.add_argument("--is-all-day", action="store_true", help="All-day task")
    task_create.add_argument("--time-zone", help="Time zone (e.g., Asia/Shanghai)")
    task_create.add_argument("--tags", help="Comma-separated tags")
    task_create.set_defaults(func=cmd_create_task)

    task_get = subparsers.add_parser("get-task", help="Get task details")
    task_get.add_argument("projectId", help="Project ID")
    task_get.add_argument("taskId", help="Task ID")
    task_get.set_defaults(func=cmd_get_task)

    task_update = subparsers.add_parser("update-task", help="Update a task")
    task_update.add_argument("taskId", help="Task ID")
    task_update.add_argument("--project-id", required=True, help="Project ID")
    task_update.add_argument("--title", help="New title")
    task_update.add_argument("--content", help="New content")
    task_update.add_argument("--due-date", help="New due date")
    task_update.add_argument("--start-date", help="New start date")
    task_update.add_argument("--priority", type=int, choices=[0, 1, 3, 5])
    task_update.add_argument("--is-all-day", type=lambda x: x.lower() == "true")
    task_update.add_argument("--tags", help="Comma-separated tags")
    task_update.set_defaults(func=cmd_update_task)

    task_complete = subparsers.add_parser("complete-task", help="Mark task as complete")
    task_complete.add_argument("projectId", help="Project ID")
    task_complete.add_argument("taskId", help="Task ID")
    task_complete.set_defaults(func=cmd_complete_task)

    task_uncomplete = subparsers.add_parser("uncomplete-task", help="Mark task as incomplete")
    task_uncomplete.add_argument("projectId", help="Project ID")
    task_uncomplete.add_argument("taskId", help="Task ID")
    task_uncomplete.set_defaults(func=cmd_uncomplete_task)

    task_delete = subparsers.add_parser("delete-task", help="Delete a task")
    task_delete.add_argument("projectId", help="Project ID")
    task_delete.add_argument("taskId", help="Task ID")
    task_delete.set_defaults(func=cmd_delete_task)

    task_move = subparsers.add_parser("move-task", help="Move task to another project")
    task_move.add_argument("taskId", help="Task ID")
    task_move.add_argument("fromProjectId", help="Source project ID")
    task_move.add_argument("toProjectId", help="Target project ID")
    task_move.set_defaults(func=cmd_move_task)

    task_filter = subparsers.add_parser("filter-tasks", help="Filter tasks with criteria")
    task_filter.add_argument("--project-ids", help="Comma-separated project IDs")
    task_filter.add_argument("--start-date", help="Filter start date")
    task_filter.add_argument("--end-date", help="Filter end date")
    task_filter.add_argument("--priority", help="Comma-separated priorities (0,1,3,5)")
    task_filter.add_argument("--tags", help="Comma-separated tags")
    task_filter.add_argument("--status", help="Comma-separated status (0=open, 2=completed)")
    task_filter.add_argument("--is-all-day", type=lambda x: x.lower() == "true")
    task_filter.set_defaults(func=cmd_filter_tasks)

    task_completed = subparsers.add_parser("completed-tasks", help="List completed tasks")
    task_completed.add_argument("--project-ids", help="Comma-separated project IDs")
    task_completed.add_argument("--start-date", help="Filter start date")
    task_completed.add_argument("--end-date", help="Filter end date")
    task_completed.add_argument("--limit", type=int, help="Maximum number of results")
    task_completed.set_defaults(func=cmd_completed_tasks)

    # Parse and execute
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Skip auth check for auth commands
    if args.command in ("auth", "auth-status", "logout"):
        args.func(args)
        return

    # For other commands, ensure authenticated
    try:
        args.func(args)
    except ValueError as e:
        # Missing credentials
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()