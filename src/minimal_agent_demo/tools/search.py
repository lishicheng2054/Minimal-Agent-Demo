from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections import Counter

_CORPUS = [
    {
        "title": "Agent runtime",
        "content": "A minimal agent loops through user input, tool calls, trace logging, and final answers.",
    },
    {
        "title": "Session memory",
        "content": "Persist tasks and recent messages so later turns can continue the same work.",
    },
    {
        "title": "Tools",
        "content": "Calculator, search, todo, and read_docs cover the required demo capabilities.",
    },
]


def mock_search(query: str) -> str:
    tokens = [token.lower() for token in query.split() if token.strip()]
    scored: list[tuple[int, dict[str, str]]] = []
    for doc in _CORPUS:
        haystack = f"{doc['title']} {doc['content']}".lower()
        score = sum(Counter(tokens)[token] for token in tokens if token in haystack)
        scored.append((score, doc))
    ranked = sorted(scored, key=lambda item: (-item[0], item[1]["title"]))
    lines = [
        f"{item['title']}: {item['content']}"
        for score, item in ranked
        if score > 0
    ]
    return "\n".join(lines) if lines else "No mock search results found."


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


search_tool = ToolSpec(
    name="search",
    description="Search a tiny mock corpus for relevant notes.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
        "additionalProperties": False,
    },
)
