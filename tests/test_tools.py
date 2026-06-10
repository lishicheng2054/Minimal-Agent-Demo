from pathlib import Path

import pytest

from minimal_agent_demo.session import SessionState
from minimal_agent_demo.tools.calculator import calculate
from minimal_agent_demo.tools.search import mock_search
from minimal_agent_demo.tools.todo import todo_tool
from minimal_agent_demo.tools.read_docs import read_docs


def test_calculator_handles_operator_precedence():
    assert calculate("2 + 3 * 4") == "14"


def test_search_returns_ranked_mock_hits():
    result = mock_search("agent session")
    assert "session" in result.lower()


def test_todo_create_and_list_flow():
    session = SessionState(session_id="demo")
    session = session.add_task("Ship demo")
    created = todo_tool(session, action="create", title="Write README")
    assert "Write README" in created


def test_read_docs_reads_repo_file(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    target = docs / "note.md"
    target.write_text("hello world", encoding="utf-8")

    assert "hello" in read_docs(tmp_path, "docs/note.md")

