#!/usr/bin/env python3
"""
Dida365 (滴答清单) OpenAPI Client

A command-line tool for managing tasks and projects in Dida365.

Usage:
    python dida_api.py <command> [options]

Commands:
    projects                    List all projects
    project <projectId>         Get project info
    project-data <projectId>    Get project with tasks
    create-project              Create a new project
    delete-project <projectId>  Delete a project

    create-task                 Create a new task
    get-task <projectId> <taskId>   Get task details
    update-task <taskId>        Update a task
    complete-task <projectId> <taskId>  Mark task complete
    delete-task <projectId> <taskId>   Delete a task
    move-task <taskId> <fromProjectId> <toProjectId>  Move task
    filter-tasks                Filter tasks with criteria
    completed-tasks             List completed tasks

Environment Variables:
    DIDA_ACCESS_TOKEN   - OAuth access token

Config File:
    ~/.dida365/config.json
    {"access_token": "your-token"}
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import urllib.request
import urllib.error
import base64

# API Configuration
API_BASE_URL = "https://api.dida365.com/open/v1"
CONFIG_FILE = Path.home() / ".dida365" / "config.json"


def get_access_token() -> str:
    """Get access token from environment or config file."""
    # Try environment variable first
    token = os.environ.get("DIDA_ACCESS_TOKEN")
    if token:
        return token

    # Try config file
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            token = config.get("access_token")
            if token:
                return token

    raise ValueError(
        "No access token found. Set DIDA_ACCESS_TOKEN environment variable "
        "or create ~/.dida365/config.json with {'access_token': 'your-token'}"
    )


def api_request(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> Any:
    """Make an API request to Dida365."""
    token = get_access_token()

    url = f"{API_BASE_URL}{endpoint}"

    # Build request
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
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"API Error {e.code}: {error_body}")


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to Dida365 format."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


def format_output(data: Any, format_type: str = "json") -> str:
    """Format output for display."""
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    return str(data)


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
    print(format_output(result))


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

    result = api_request("POST", f"/task/{args.taskId}", data=data)
    print(format_output(result))


def cmd_complete_task(args):
    """Mark task as complete."""
    result = api_request(
        "POST", f"/project/{args.projectId}/task/{args.taskId}/complete"
    )
    print(format_output({"success": True, "message": "Task completed"}))


def cmd_delete_task(args):
    """Delete a task."""
    result = api_request("DELETE", f"/project/{args.projectId}/task/{args.taskId}")
    print(format_output({"success": True, "message": "Task deleted"}))


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
        data["projectIds"] = args.project_ids.split(",")
    if args.start_date:
        data["startDate"] = args.start_date
    if args.end_date:
        data["endDate"] = args.end_date
    if args.priority:
        data["priority"] = [int(p) for p in args.priority.split(",")]
    if args.tags:
        data["tag"] = args.tags.split(",")
    if args.status:
        data["status"] = [int(s) for s in args.status.split(",")]

    result = api_request("POST", "/task/filter", data=data)
    print(format_output(result))


def cmd_completed_tasks(args):
    """List completed tasks."""
    data = {}

    if args.project_ids:
        data["projectIds"] = args.project_ids.split(",")
    if args.start_date:
        data["startDate"] = args.start_date
    if args.end_date:
        data["endDate"] = args.end_date

    result = api_request("POST", "/task/completed", data=data)
    print(format_output(result))


# ============================================================================
# OAuth Helper
# ============================================================================


def cmd_oauth_token(args):
    """Exchange authorization code for access token."""
    import urllib.parse

    # Build credentials for Basic Auth
    credentials = base64.b64encode(
        f"{args.client_id}:{args.client_secret}".encode()
    ).decode()

    # Build request body
    body = urllib.parse.urlencode(
        {
            "code": args.code,
            "grant_type": "authorization_code",
            "scope": "tasks:read tasks:write",
            "redirect_uri": args.redirect_uri,
        }
    )

    url = "https://dida365.com/oauth/token"
    req = urllib.request.Request(
        url,
        data=body.encode(),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(format_output(result))

            if args.save:
                config_dir = CONFIG_FILE.parent
                config_dir.mkdir(parents=True, exist_ok=True)
                with open(CONFIG_FILE, "w") as f:
                    json.dump({"access_token": result["access_token"]}, f, indent=2)
                print(f"\nToken saved to {CONFIG_FILE}")

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"OAuth Error {e.code}: {error_body}")


def cmd_oauth_url(args):
    """Generate OAuth authorization URL."""
    import urllib.parse

    params = {
        "scope": "tasks:read tasks:write",
        "client_id": args.client_id,
        "state": args.state or "random_state",
        "redirect_uri": args.redirect_uri,
        "response_type": "code",
    }

    url = f"https://dida365.com/oauth/authorize?{urllib.parse.urlencode(params)}"
    print("Authorization URL:")
    print(url)
    print("\nAfter authorization, you will be redirected to your redirect_uri with a 'code' parameter.")
    print("Use 'oauth-token' command to exchange the code for an access token.")


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Dida365 (滴答清单) API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Project commands
    proj_list = subparsers.add_parser("projects", help="List all projects")
    proj_list.set_defaults(func=cmd_projects)

    proj_get = subparsers.add_parser("project", help="Get project info")
    proj_get.add_argument("projectId", help="Project ID")
    proj_get.set_defaults(func=cmd_project)

    proj_data = subparsers.add_parser("project-data", help="Get project with tasks")
    proj_data.add_argument("projectId", help="Project ID")
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
    task_create.add_argument("--due-date", help="Due date (format: yyyy-MM-dd'T'HH:mm:ssZ)")
    task_create.add_argument("--start-date", help="Start date")
    task_create.add_argument("--priority", type=int, choices=[0, 1, 3, 5], help="Priority: 0=None, 1=Low, 3=Medium, 5=High")
    task_create.add_argument("--is-all-day", action="store_true", help="All-day task")
    task_create.add_argument("--time-zone", help="Time zone (e.g., Asia/Shanghai)")
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
    task_update.set_defaults(func=cmd_update_task)

    task_complete = subparsers.add_parser("complete-task", help="Mark task as complete")
    task_complete.add_argument("projectId", help="Project ID")
    task_complete.add_argument("taskId", help="Task ID")
    task_complete.set_defaults(func=cmd_complete_task)

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
    task_filter.set_defaults(func=cmd_filter_tasks)

    task_completed = subparsers.add_parser("completed-tasks", help="List completed tasks")
    task_completed.add_argument("--project-ids", help="Comma-separated project IDs")
    task_completed.add_argument("--start-date", help="Filter start date")
    task_completed.add_argument("--end-date", help="Filter end date")
    task_completed.set_defaults(func=cmd_completed_tasks)

    # OAuth commands
    oauth_url = subparsers.add_parser("oauth-url", help="Generate OAuth authorization URL")
    oauth_url.add_argument("--client-id", required=True, help="OAuth client ID")
    oauth_url.add_argument("--redirect-uri", required=True, help="Redirect URI")
    oauth_url.add_argument("--state", help="State parameter")
    oauth_url.set_defaults(func=cmd_oauth_url)

    oauth_token = subparsers.add_parser("oauth-token", help="Exchange code for access token")
    oauth_token.add_argument("--client-id", required=True, help="OAuth client ID")
    oauth_token.add_argument("--client-secret", required=True, help="OAuth client secret")
    oauth_token.add_argument("--code", required=True, help="Authorization code")
    oauth_token.add_argument("--redirect-uri", required=True, help="Redirect URI")
    oauth_token.add_argument("--save", action="store_true", help="Save token to config file")
    oauth_token.set_defaults(func=cmd_oauth_token)

    # Parse and execute
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()