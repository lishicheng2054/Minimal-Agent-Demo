from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from minimal_agent_demo.session import SessionState


def todo_tool(session: SessionState, action: str, title: str | None = None, task_id: int | None = None) -> str:
    if action == "create":
        if not title:
            raise ValueError("title is required for create")
        updated = session.add_task(title=title)
        return f"Created task #{updated.tasks[-1].id}: {title}"
    if action == "list":
        if not session.tasks:
            return "No tasks yet."
        return "\n".join(f"#{task.id} [{task.status}] {task.title}" for task in session.tasks)
    if action == "update":
        if task_id is None:
            raise ValueError("task_id is required for update")
        updated = session.update_task(task_id, status="done")
        return f"Updated task #{task_id} to done."
    raise ValueError(f"Unknown action: {action}")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


todo_tool_spec = ToolSpec(
    name="todo",
    description="Create, list, or update tasks inside the current session.",
    parameters={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["create", "list", "update"]},
            "title": {"type": "string"},
            "task_id": {"type": "integer"},
            "status": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["action"],
        "additionalProperties": False,
    },
)
