from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


@dataclass
class TraceEvent:
    step: int
    kind: str
    details: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TraceRecorder:
    events: list[TraceEvent] = field(default_factory=list)

    def add(self, step: int, kind: str, **details: Any) -> None:
        self.events.append(TraceEvent(step=step, kind=kind, details=details))

    def to_dict(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self.events]

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class TurnLog:
    session_id: str
    user_input: str
    final_answer: str
    plan: str
    reflection: str
    trace: list[dict[str, Any]]
    session_summary: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_input": self.user_input,
            "final_answer": self.final_answer,
            "plan": self.plan,
            "reflection": self.reflection,
            "trace": [dict(item) for item in self.trace],
            "session_summary": self.session_summary,
            "timestamp": self.timestamp,
        }

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
