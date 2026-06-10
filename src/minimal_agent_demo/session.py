from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Task:
    id: int
    title: str
    status: str = "open"
    notes: str = ""


@dataclass
class SessionState:
    session_id: str
    messages: list[Message] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    last_plan: str = ""
    last_reflection: str = ""
    last_trace: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_message(self, role: str, content: str) -> "SessionState":
        updated = SessionState(
            session_id=self.session_id,
            messages=[*self.messages, Message(role=role, content=content)],
            tasks=[*self.tasks],
            attachments=[*self.attachments],
            last_plan=self.last_plan,
            last_reflection=self.last_reflection,
            last_trace=[*self.last_trace],
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        return updated

    def add_task(self, title: str, status: str = "open", notes: str = "") -> "SessionState":
        next_id = 1 if not self.tasks else max(task.id for task in self.tasks) + 1
        updated = SessionState(
            session_id=self.session_id,
            messages=[*self.messages],
            tasks=[*self.tasks, Task(id=next_id, title=title, status=status, notes=notes)],
            attachments=[*self.attachments],
            last_plan=self.last_plan,
            last_reflection=self.last_reflection,
            last_trace=[*self.last_trace],
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        return updated

    def update_task(self, task_id: int, *, status: str | None = None, notes: str | None = None) -> "SessionState":
        updated_tasks: list[Task] = []
        for task in self.tasks:
            if task.id != task_id:
                updated_tasks.append(task)
                continue
            updated_tasks.append(
                Task(
                    id=task.id,
                    title=task.title,
                    status=status or task.status,
                    notes=notes if notes is not None else task.notes,
                )
            )
        return SessionState(
            session_id=self.session_id,
            messages=[*self.messages],
            tasks=updated_tasks,
            attachments=[*self.attachments],
            last_plan=self.last_plan,
            last_reflection=self.last_reflection,
            last_trace=[*self.last_trace],
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def add_attachment(self, attachment: str) -> "SessionState":
        return SessionState(
            session_id=self.session_id,
            messages=[*self.messages],
            tasks=[*self.tasks],
            attachments=[*self.attachments, attachment],
            last_plan=self.last_plan,
            last_reflection=self.last_reflection,
            last_trace=[*self.last_trace],
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def with_artifacts(
        self,
        *,
        last_plan: str | None = None,
        last_reflection: str | None = None,
        last_trace: list[dict[str, Any]] | None = None,
    ) -> "SessionState":
        return SessionState(
            session_id=self.session_id,
            messages=[*self.messages],
            tasks=[*self.tasks],
            attachments=[*self.attachments],
            last_plan=self.last_plan if last_plan is None else last_plan,
            last_reflection=self.last_reflection if last_reflection is None else last_reflection,
            last_trace=[*self.last_trace] if last_trace is None else [dict(item) for item in last_trace],
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def summary(self, max_messages: int = 6) -> str:
        recent_messages = self.messages[-max_messages:]
        message_lines = [f"{item.role}: {item.content}" for item in recent_messages]
        task_lines = [
            f"#{task.id} [{task.status}] {task.title}"
            + (f" - {task.notes}" if task.notes else "")
            for task in self.tasks
        ]
        artifact_lines = [
            f"Plan: {self.last_plan}" if self.last_plan else "Plan: (none yet)",
            f"Reflection: {self.last_reflection}" if self.last_reflection else "Reflection: (none yet)",
            f"Trace events: {len(self.last_trace)}",
        ]
        attachment_lines = [f"- {item}" for item in self.attachments] if self.attachments else ["No attachments yet."]
        if not message_lines:
            message_lines = ["No messages yet."]
        if not task_lines:
            task_lines = ["No tasks yet."]
        return "\n".join([
            "Messages:",
            *message_lines,
            "Tasks:",
            *task_lines,
            "Artifacts:",
            *artifact_lines,
            "Attachments:",
            *attachment_lines,
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [asdict(message) for message in self.messages],
            "tasks": [asdict(task) for task in self.tasks],
            "attachments": [item for item in self.attachments],
            "last_plan": self.last_plan,
            "last_reflection": self.last_reflection,
            "last_trace": [dict(item) for item in self.last_trace],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        return cls(
            session_id=data["session_id"],
            messages=[Message(**item) for item in data.get("messages", [])],
            tasks=[Task(**item) for item in data.get("tasks", [])],
            attachments=list(data.get("attachments", [])),
            last_plan=data.get("last_plan", ""),
            last_reflection=data.get("last_reflection", ""),
            last_trace=[dict(item) for item in data.get("last_trace", [])],
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


class SessionStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, session_id: str) -> Path:
        return self.root / f"{session_id}.json"

    def load_or_create(self, session_id: str) -> SessionState:
        path = self._path(session_id)
        if path.exists():
            return SessionState.from_dict(json.loads(path.read_text(encoding="utf-8")))
        return SessionState(session_id=session_id)

    def save(self, session: SessionState) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path(session.session_id)
        path.write_text(json.dumps(session.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
