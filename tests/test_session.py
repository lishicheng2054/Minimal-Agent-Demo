from pathlib import Path

from minimal_agent_demo.session import SessionState, SessionStore


def test_session_persists_tasks(tmp_path: Path):
    store = SessionStore(tmp_path)
    session = store.load_or_create("demo")
    session = session.add_task("Write README", status="open")
    store.save(session)

    reloaded = store.load_or_create("demo")
    assert reloaded.tasks[0].title == "Write README"


def test_session_summary_includes_recent_messages_and_tasks():
    session = SessionState(session_id="demo")
    session = session.add_message("user", "start task")
    session = session.add_task("Ship demo")

    summary = session.summary()
    assert "Ship demo" in summary
    assert "start task" in summary

