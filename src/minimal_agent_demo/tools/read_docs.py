from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def read_docs(root: Path, path: str, query: str | None = None, max_chars: int = 1200) -> str:
    target = (root / path).resolve()
    root_resolved = root.resolve()
    if root_resolved not in target.parents and target != root_resolved:
        raise ValueError("Path escapes docs root")
    text = target.read_text(encoding="utf-8")
    if query:
        lowered = query.lower()
        lines = [line for line in text.splitlines() if lowered in line.lower()]
        text = "\n".join(lines) if lines else text
    return text[:max_chars]


def summarize_file(root: Path, path: str, max_chars: int = 500) -> str:
    content = read_docs(root, path, max_chars=max_chars)
    return f"{path}: {content[:max_chars]}"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


read_docs_tool = ToolSpec(
    name="read_docs",
    description="Read local markdown or text docs from the repository.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "query": {"type": "string"},
            "max_chars": {"type": "integer", "minimum": 1},
        },
        "required": ["path"],
        "additionalProperties": False,
    },
)
