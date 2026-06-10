from pathlib import Path
from types import SimpleNamespace

from minimal_agent_demo.cli import InteractiveCLI, parse_command, is_command


class FakeRuntime:
    def __init__(self):
        self.session_store = SimpleNamespace(
            load_or_create=lambda session_id: SimpleNamespace(
                messages=[],
                tasks=[],
                attachments=[],
                last_plan="",
                last_reflection="",
                summary=lambda: "summary",
            ),
            save=lambda session: None,
        )
        self.tool_names = lambda: ["calculator", "search", "todo", "read_docs"]
        self.docs_root = Path("C:/Users/lsc15/Desktop/AI agent项目/mini-agent-demo")
        self.calls = []

    def run_turn(self, session_id, text):
        self.calls.append((session_id, text))
        return SimpleNamespace(
            session_id=session_id,
            final_answer="done",
            plan="plan text",
            reflection="reflection text",
            session_summary="summary",
            trace=[{"step": 0, "kind": "final_answer", "details": {"content": "done"}}],
        )

    def _tool_call_payload(self, tool_name, arguments, session):
        return "file contents", session


class FakeSession:
    def __init__(self):
        self.messages = []
        self.tasks = []
        self.attachments = []

    def summary(self):
        return "summary"

    def add_attachment(self, text):
        updated = FakeSession()
        updated.messages = list(self.messages)
        updated.tasks = list(self.tasks)
        updated.attachments = [*self.attachments, text]
        return updated


def test_parse_command_switches_session():
    command = parse_command("/session demo-2")
    assert command.name == "session"
    assert command.args == ["demo-2"]


def test_parse_command_reads_file_argument():
    command = parse_command("/read README.md")
    assert command.name == "read"
    assert command.args == ["README.md"]


def test_is_command_detects_leading_slash():
    assert is_command("/trace")
    assert not is_command("hello")


def test_interactive_cli_switches_session():
    cli = InteractiveCLI(FakeRuntime(), session_id="demo")
    assert cli.run_command("/session demo-2") == "已切换到会话: demo-2"
    assert cli.session_id == "demo-2"


def test_interactive_cli_formats_result():
    cli = InteractiveCLI(FakeRuntime(), session_id="demo")
    output = cli.submit_message("hello")
    assert output == "done"


def test_interactive_cli_state_command_shows_summary():
    cli = InteractiveCLI(FakeRuntime(), session_id="demo")
    output = cli.run_command("/state")
    assert "会话: demo" in output
    assert "最近消息:" in output


def test_interactive_cli_attach_command():
    cli = InteractiveCLI(FakeRuntime(), session_id="demo")
    output = cli.run_command("/attach README.md")
    assert "已附加文件" in output


def test_interactive_cli_context_alias():
    cli = InteractiveCLI(FakeRuntime(), session_id="demo")
    output = cli.run_command("/context")
    assert "会话: demo" in output


def test_interactive_cli_state_shows_plan_and_reflection():
    runtime = FakeRuntime()
    runtime.session_store = SimpleNamespace(
        load_or_create=lambda session_id: SimpleNamespace(
            messages=[],
            tasks=[],
            attachments=[],
            last_plan="先用计算器验证表达式",
            last_reflection="结果可靠",
            summary=lambda: "summary",
        ),
        save=lambda session: None,
    )
    cli = InteractiveCLI(runtime, session_id="demo")
    output = cli.run_command("/state")
    assert "最近计划:" in output
    assert "最近反思:" in output


def test_interactive_cli_verbose_mode_shows_details():
    cli = InteractiveCLI(FakeRuntime(), session_id="demo", verbose=True)
    output = cli.submit_message("hello")
    assert "=== Agent Result ===" in output
    assert "plan:" in output
    assert "final answer:" in output
    assert "done" in output


def test_interactive_cli_default_mode_is_plain_answer():
    cli = InteractiveCLI(FakeRuntime(), session_id="demo")
    output = cli.submit_message("hello")
    assert output == "done"
