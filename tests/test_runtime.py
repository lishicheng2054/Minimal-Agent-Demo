from pathlib import Path
from types import SimpleNamespace

from minimal_agent_demo.config import Settings
from minimal_agent_demo.runtime import AgentRuntime


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


def _tool_call(call_id: str, name: str, arguments: str):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def test_runtime_tool_loop_returns_final_answer(tmp_path: Path):
    plan = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Plan: use calculator", tool_calls=None))])
    first = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[_tool_call("call_1", "calculator", '{"expression":"2+3*4"}')],
                )
            )
        ]
    )
    second = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="14", tool_calls=None))]
    )
    reflection = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Looks good", tool_calls=None))])
    client = FakeClient([plan, first, second, reflection])
    settings = Settings(
        api_key="test",
        model="gpt-test",
        base_url="",
        session_dir=tmp_path / "sessions",
        docs_root=tmp_path,
    )
    runtime = AgentRuntime(client, settings, max_steps=3)

    result = runtime.run_turn("demo", "What is 2 + 3 * 4?")

    assert result.final_answer == "14"
    assert any(event["kind"] == "tool_call" for event in result.trace)
    assert result.plan is not None
    assert result.reflection is not None


def test_runtime_uses_session_memory_on_second_turn(tmp_path: Path):
    plan_1 = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Plan: create todo", tool_calls=None))])
    first = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[_tool_call("call_1", "todo", '{"action":"create","title":"Write README"}')],
                )
            )
        ]
    )
    second = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Task created.", tool_calls=None))])
    reflection_1 = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Looks good", tool_calls=None))])
    plan_2 = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Plan: check progress", tool_calls=None))])
    third = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Task is in progress.", tool_calls=None))])
    reflection_2 = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Looks good", tool_calls=None))])
    client = FakeClient([plan_1, first, second, reflection_1, plan_2, third, reflection_2])
    settings = Settings(
        api_key="test",
        model="gpt-test",
        base_url="",
        session_dir=tmp_path / "sessions",
        docs_root=tmp_path,
    )
    runtime = AgentRuntime(client, settings, max_steps=3)

    runtime.run_turn("demo", "Please create a task to write the README.")
    runtime.run_turn("demo", "How is the task going?")

    second_call = client.chat.completions.calls[-3]
    joined = "\n".join(str(item) for item in second_call["messages"])
    assert "Write README" in joined


def test_runtime_result_includes_plan_and_reflection_fields(tmp_path: Path):
    first = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Plan: use calculator", tool_calls=None))])
    second = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="42", tool_calls=None))])
    third = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Looks good", tool_calls=None))])
    client = FakeClient([first, second, third])
    settings = Settings(api_key="test", model="gpt-test", base_url="", session_dir=tmp_path / "sessions", docs_root=tmp_path)
    runtime = AgentRuntime(client, settings, max_steps=3)

    result = runtime.run_turn("demo", "What is 6 * 7?")

    assert result.plan
    assert result.reflection


def test_runtime_uses_text_only_calls_for_plan_and_reflection(tmp_path: Path):
    plan = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Plan: use calculator", tool_calls=None))])
    first = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[_tool_call("call_1", "calculator", '{"expression":"8*5"}')],
                )
            )
        ]
    )
    second = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="40", tool_calls=None))])
    reflection = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Looks good", tool_calls=None))])
    client = FakeClient([plan, first, second, reflection])
    settings = Settings(api_key="test", model="gpt-test", base_url="", session_dir=tmp_path / "sessions", docs_root=tmp_path)
    runtime = AgentRuntime(client, settings, max_steps=3)

    runtime.run_turn("demo", "What is 8 * 5?")

    assert client.chat.completions.calls[0]["tool_choice"] == "none"
    assert client.chat.completions.calls[1]["tool_choice"] == "auto"
    assert client.chat.completions.calls[-1]["tool_choice"] == "none"


def test_runtime_persists_turn_artifacts_in_session_state(tmp_path: Path):
    plan = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Plan: create a todo", tool_calls=None))])
    first = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[_tool_call("call_1", "todo", '{"action":"create","title":"Write docs"}')],
                )
            )
        ]
    )
    second = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Task created.", tool_calls=None))])
    reflection = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Looks good", tool_calls=None))])
    client = FakeClient([plan, first, second, reflection])
    settings = Settings(api_key="test", model="gpt-test", base_url="", session_dir=tmp_path / "sessions", docs_root=tmp_path)
    runtime = AgentRuntime(client, settings, max_steps=3)

    runtime.run_turn("demo", "Please create a task.")

    session = runtime.session_store.load_or_create("demo")
    assert session.last_plan == "Plan: create a todo"
    assert session.last_reflection == "Looks good"
    assert session.last_trace[-1]["kind"] == "final_answer"


def test_runtime_builds_client_with_base_url(tmp_path: Path, monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **_: None))

    import minimal_agent_demo.config as config_module

    monkeypatch.setitem(config_module.__dict__, "OpenAI", FakeOpenAI)

    settings = Settings(
        api_key="test",
        model="gpt-test",
        base_url="https://example.com/v1",
        session_dir=tmp_path / "sessions",
        docs_root=tmp_path,
    )
    runtime = AgentRuntime(None, settings)

    runtime._make_client()

    assert captured["api_key"] == "test"
    assert captured["base_url"] == "https://example.com/v1"
