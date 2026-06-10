from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import json
from time import sleep

import httpx

from minimal_agent_demo.config import Settings
from minimal_agent_demo.prompts import SYSTEM_PROMPT, build_plan_prompt, build_reflection_prompt, build_session_prompt
from minimal_agent_demo.session import SessionState, SessionStore
from minimal_agent_demo.trace import TraceRecorder
from minimal_agent_demo.tools import (
    calculate,
    calculator_tool,
    mock_search,
    read_docs,
    read_docs_tool,
    search_tool,
    todo_tool,
    todo_tool_spec,
)


@dataclass
class AgentResult:
    session_id: str
    final_answer: str
    trace: list[dict[str, Any]]
    session_summary: str
    plan: str
    reflection: str


class AgentRuntime:
    def __init__(
        self,
        client: Any | None,
        settings: Settings,
        session_store: SessionStore | None = None,
        docs_root: Path | None = None,
        max_steps: int = 6,
    ) -> None:
        self.settings = settings
        self.client = client
        self.session_store = session_store or SessionStore(settings.session_dir)
        self.docs_root = docs_root or settings.docs_root
        self.max_steps = max_steps
        self._tool_specs = {
            "calculator": calculator_tool,
            "search": search_tool,
            "todo": todo_tool_spec,
            "read_docs": read_docs_tool,
        }

    @classmethod
    def for_tests(cls) -> "AgentRuntime":
        fake_settings = Settings(
            api_key="test",
            model="gpt-test",
            session_dir=Path("tests-data/sessions"),
            docs_root=Path("."),
            base_url="",
        )
        return cls(client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: None))), settings=fake_settings)

    def tool_names(self) -> list[str]:
        return list(self._tool_specs.keys())

    def run_turn(self, session_id: str, user_input: str) -> AgentResult:
        session = self._load_session(session_id)
        working_session = session.add_message("user", user_input)
        trace = TraceRecorder()
        trace.add(0, "user_input", content=user_input, session_id=session_id)

        attachments_summary = self._attachments_summary(working_session)
        plan_prompt = build_plan_prompt(user_input, attachments_summary)
        messages = self._messages_for_session(working_session, plan_prompt)
        final_answer = ""
        tool_outputs_summary: list[str] = []
        plan_text = ""
        reflection_text = ""
        step = 0

        try:
            plan_response = self._call_llm(messages, tool_choice="none")
            plan_message = self._extract_message(plan_response)
            if plan_message is not None:
                plan_text = (getattr(plan_message, "content", None) or "").strip()
                if plan_text:
                    trace.add(0, "plan", content=plan_text)
                    working_session = working_session.with_artifacts(last_plan=plan_text)
                    self._save_session(working_session)
            messages = self._messages_for_session(working_session)
            for step in range(1, self.max_steps + 1):
                response = self._call_llm(messages)
                message = self._extract_message(response)
                if message is None:
                    break

                tool_calls = getattr(message, "tool_calls", None) or []
                text = (getattr(message, "content", None) or "").strip()
                if text:
                    trace.add(step, "assistant_draft", content=text)

                if not tool_calls:
                    final_answer = text
                    break

                messages.append({"role": "assistant", "content": text, "tool_calls": tool_calls})
                tool_outputs: list[dict[str, Any]] = []
                for call in tool_calls:
                    tool_name = call.function.name
                    args = json.loads(call.function.arguments) if isinstance(call.function.arguments, str) else call.function.arguments
                    output, working_session = self._tool_call_payload(tool_name, args, working_session)
                    trace.add(step, "tool_call", tool=tool_name, arguments=args, output=output)
                    tool_outputs_summary.append(f"{tool_name}: {output}")
                    tool_outputs.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": tool_name,
                            "content": output,
                        }
                    )

                messages.extend(tool_outputs)
                self._save_session(working_session)
                continue
        except Exception as exc:  # noqa: BLE001
            final_answer = self._format_runtime_error(exc)
            trace.add(0, "error", message=final_answer)
            working_session = working_session.add_message("assistant", final_answer)
            self._save_session(working_session)
            return AgentResult(
                session_id=session_id,
                final_answer=final_answer,
                trace=trace.to_dict(),
                session_summary=working_session.summary(),
                plan=plan_text,
                reflection=reflection_text,
            )

        if not final_answer:
            final_answer = "I could not finish within the step limit."

        reflection_prompt = build_reflection_prompt(final_answer, "\n".join(tool_outputs_summary))
        reflection_messages = self._messages_for_session(working_session, reflection_prompt)
        try:
            reflection_response = self._call_llm(reflection_messages, tool_choice="none")
            reflection_message = self._extract_message(reflection_response)
            if reflection_message is not None:
                reflection_text = (getattr(reflection_message, "content", None) or "").strip()
                if reflection_text:
                    trace.add(self.max_steps + 1, "reflection", content=reflection_text)
        except Exception:
            pass

        trace.add(step if "step" in locals() else 0, "final_answer", content=final_answer)
        working_session = working_session.add_message("assistant", final_answer)
        working_session = working_session.with_artifacts(
            last_plan=plan_text,
            last_reflection=reflection_text,
            last_trace=trace.to_dict(),
        )
        self._save_session(working_session)
        return AgentResult(
            session_id=session_id,
            final_answer=final_answer,
            trace=trace.to_dict(),
            session_summary=working_session.summary(),
            plan=plan_text,
            reflection=reflection_text,
        )

    def _load_session(self, session_id: str) -> SessionState:
        return self.session_store.load_or_create(session_id)

    def _save_session(self, session: SessionState) -> None:
        self.session_store.save(session)

    def _tool_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                },
            }
            for spec in self._tool_specs.values()
        ]

    def _messages_for_session(self, session: SessionState, extra_prompt: str | None = None) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": build_session_prompt(session.summary())},
            *(
                [{"role": "system", "content": extra_prompt}]
                if extra_prompt
                else []
            ),
            *(
                [{"role": "system", "content": self._attachments_summary_message(session)}]
                if session.attachments
                else []
            ),
            *[{"role": message.role, "content": message.content} for message in session.messages],
        ]

    def _attachments_summary_message(self, session: SessionState) -> str:
        return "Attached files:\n" + "\n".join(f"- {item}" for item in session.attachments)

    def _attachments_summary(self, session: SessionState) -> str:
        return "\n".join(session.attachments)

    def session_summary(self, session_id: str) -> str:
        return self._load_session(session_id).summary()

    def session_messages(self, session_id: str) -> list[dict[str, str]]:
        session = self._load_session(session_id)
        return [{"role": message.role, "content": message.content} for message in session.messages]

    def session_attachments(self, session_id: str) -> list[str]:
        return list(self._load_session(session_id).attachments)

    def _call_llm(self, messages: list[dict[str, Any]], tool_choice: str = "auto") -> Any:
        if not self.settings.api_key:
            raise RuntimeError(
                "Missing OPENAI_API_KEY. Set it in .env or environment variables before sending a message."
            )
        if self.client is None:
            self.client = self._make_client()
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                return self.client.chat.completions.create(
                    model=self.settings.model,
                    messages=messages,
                    tools=self._tool_schema(),
                    tool_choice=tool_choice,
                    temperature=0.2,
                )
            except (httpx.HTTPError, RuntimeError) as exc:
                last_error = exc
                if attempt == 0:
                    sleep(1)
                    continue
                raise RuntimeError(self._format_runtime_error(exc)) from None
        raise RuntimeError(self._format_runtime_error(last_error or RuntimeError("Unknown LLM error"))) from None

    def _make_client(self) -> Any:
        from minimal_agent_demo.config import make_client

        return make_client(self.settings)

    def _extract_message(self, response: Any) -> Any:
        if response is None:
            return None
        return response.choices[0].message

    def _format_runtime_error(self, exc: Exception) -> str:
        message = str(exc)
        lower = message.lower()
        if "openaiapikey" in lower or "missing credentials" in lower:
            return "缺少 OPENAI_API_KEY，请先配置 .env 或环境变量。"
        if "connection error" in lower or "connect error" in lower:
            if self.settings.base_url:
                return (
                    "连接到兼容 OpenAI 的接口失败。请检查 OPENAI_BASE_URL、API Key、网络和模型名是否正确。"
                )
            return "连接 OpenAI 失败。请检查网络、代理、VPN、API Key 和防火墙设置，然后重试。"
        if "winerror 10054" in lower or "connecterror" in lower or "timeout" in lower:
            if self.settings.base_url:
                return "连接兼容 OpenAI 的接口失败，请检查 base_url、网络和 API Key。"
            return "网络连接 OpenAI 失败。请检查网络、代理、VPN、API Key 和防火墙设置，然后重试。"
        return f"运行失败: {message}"

    def _tool_call_payload(self, tool_name: str, arguments: dict[str, Any], session: SessionState) -> tuple[str, SessionState]:
        try:
            if tool_name == "calculator":
                return calculate(arguments["expression"]), session
            if tool_name == "search":
                return mock_search(arguments["query"]), session
            if tool_name == "todo":
                action = arguments["action"]
                output = todo_tool(
                    session=session,
                    action=action,
                    title=arguments.get("title"),
                    task_id=arguments.get("task_id"),
                )
                if action == "create" and arguments.get("title"):
                    session = session.add_task(arguments["title"])
                elif action == "update" and arguments.get("task_id") is not None:
                    session = session.update_task(arguments["task_id"], status=arguments.get("status"), notes=arguments.get("notes"))
                return output, session
            if tool_name == "read_docs":
                return (
                    read_docs(
                        self.docs_root,
                        arguments["path"],
                        query=arguments.get("query"),
                        max_chars=arguments.get("max_chars", 1200),
                    ),
                    session,
                )
            return f"Unknown tool: {tool_name}", session
        except Exception as exc:  # noqa: BLE001
            return f"Tool error: {exc}", session
