from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import shlex
from pathlib import Path

from minimal_agent_demo.runtime import AgentRuntime
from minimal_agent_demo.tools.read_docs import summarize_file
from minimal_agent_demo.trace import TurnLog


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    args: list[str]


def is_command(text: str) -> bool:
    return text.strip().startswith("/")


def parse_command(text: str) -> ParsedCommand:
    parts = shlex.split(text.strip())
    if not parts:
        return ParsedCommand(name="", args=[])
    return ParsedCommand(name=parts[0].lstrip("/"), args=parts[1:])


class InteractiveCLI:
    def __init__(self, runtime: AgentRuntime, session_id: str = "demo", verbose: bool = False) -> None:
        self.runtime = runtime
        self.session_id = session_id
        self.verbose = verbose
        self._should_exit = False
        self._handlers: dict[str, Callable[[list[str]], str]] = {
            "session": self._handle_session,
            "new": self._handle_new,
            "history": self._handle_history,
            "trace": self._handle_trace,
            "tools": self._handle_tools,
            "memory": self._handle_memory,
            "state": self._handle_state,
            "context": self._handle_state,
            "attach": self._handle_attach,
            "read": self._handle_read,
            "help": self._handle_help,
            "exit": self._handle_exit,
            "quit": self._handle_exit,
        }

    @property
    def should_exit(self) -> bool:
        return self._should_exit

    def status_line(self) -> str:
        return f"[session={self.session_id}] [commands=/help /history /trace /tools /memory /state /attach /read /new /session /exit]"

    def run_command(self, text: str) -> str:
        command = parse_command(text)
        handler = self._handlers.get(command.name)
        if handler is None:
            return f"未知命令: {command.name}. 输入 /help 查看可用命令。"
        return handler(command.args)

    def submit_message(self, text: str) -> str:
        result = self.runtime.run_turn(self.session_id, text)
        self._save_turn_log(text, result)
        return self._format_result(result)

    def _load_session(self):
        return self.runtime.session_store.load_or_create(self.session_id)

    def _handle_session(self, args: list[str]) -> str:
        if not args:
            return f"当前会话: {self.session_id}"
        self.session_id = args[0]
        return f"已切换到会话: {self.session_id}"

    def _handle_new(self, args: list[str]) -> str:
        self.session_id = args[0] if args else "demo"
        return f"已创建并切换到新会话: {self.session_id}"

    def _handle_history(self, args: list[str]) -> str:
        session = self._load_session()
        if not session.messages:
            return "暂无历史消息。"
        lines = ["历史消息:"]
        for item in session.messages[-10:]:
            lines.append(f"- {item.role}: {item.content}")
        return "\n".join(lines)

    def _handle_trace(self, args: list[str]) -> str:
        session = self._load_session()
        if not getattr(session, "last_trace", []):
            return "暂无 trace。请先发送一条消息。"
        lines = ["最近一次 trace:"]
        for event in session.last_trace:
            lines.append(f"- step {event['step']}: {event['kind']}")
            details = {k: v for k, v in event["details"].items() if k != "session_id"}
            if details:
                lines.append(f"  {details}")
        return "\n".join(lines)

    def _handle_tools(self, args: list[str]) -> str:
        return "可用工具: " + ", ".join(self.runtime.tool_names())

    def _handle_memory(self, args: list[str]) -> str:
        return "当前 memory 摘要:\n" + self.runtime.session_summary(self.session_id)

    def _handle_state(self, args: list[str]) -> str:
        session = self._load_session()
        lines = [
            f"会话: {self.session_id}",
            "摘要:",
            session.summary(),
            "",
            "最近消息:",
        ]
        messages = getattr(self.runtime, "session_messages", lambda _sid: [])(self.session_id)
        for item in messages[-10:]:
            if isinstance(item, dict):
                lines.append(f"- {item.get('role')}: {item.get('content')}")
            else:
                lines.append(f"- {getattr(item, 'role', 'unknown')}: {getattr(item, 'content', '')}")
        if getattr(session, "last_plan", ""):
            lines.extend(["", "最近计划:", session.last_plan])
        if getattr(session, "last_reflection", ""):
            lines.extend(["", "最近反思:", session.last_reflection])
        return "\n".join(lines)

    def _handle_read(self, args: list[str]) -> str:
        if not args:
            return "请提供文件路径，例如 /read README.md"
        session = self._load_session()
        output, _ = self.runtime._tool_call_payload(  # noqa: SLF001
            "read_docs",
            {"path": args[0], "query": None, "max_chars": 1200},
            session,
        )
        return output

    def _handle_attach(self, args: list[str]) -> str:
        if not args:
            return "请提供文件路径，例如 /attach README.md"
        path = args[0]
        session = self._load_session()
        summary = summarize_file(self.runtime.docs_root, path)
        updated = session.add_attachment(summary) if hasattr(session, "add_attachment") else session
        if hasattr(updated, "add_attachment") and updated is session:
            updated = updated.add_attachment(summary)
        self.runtime.session_store.save(updated)
        return f"已附加文件: {path}\n{summary}"

    def _handle_help(self, args: list[str]) -> str:
        return (
            "可用命令:\n"
            "/session <id>  切换到已有会话\n"
            "/new [id]      创建/切换新会话\n"
            "/history       查看最近消息\n"
            "/trace         查看 trace 说明\n"
            "/tools         查看可用工具\n"
            "/memory        查看当前 memory 摘要\n"
            "/state         查看当前会话状态\n"
            "/attach <path> 附加本地文件到会话上下文\n"
            "/read <path>   读取本地文档\n"
            "/exit          退出"
        )

    def _handle_exit(self, args: list[str]) -> str:
        self._should_exit = True
        return "退出。"

    def _format_result(self, result) -> str:
        answer = getattr(result, "final_answer", "").strip()
        if self.verbose:
            lines = [
                "",
                "=== Agent Result ===",
                f"session: {result.session_id}",
                "final answer:",
                f"  assistant> {answer}",
                "plan:",
                getattr(result, "plan", "（无计划）") or "（无计划）",
                "session summary:",
                getattr(result, "session_summary", "（无会话摘要）") or "（无会话摘要）",
                "reflection:",
                getattr(result, "reflection", "（无反思）") or "（无反思）",
                f"trace events: {len(result.trace)}",
                "trace log file: data/logs/",
            ]
            return "\n".join(lines)
        return answer or "（无回复）"

    def _save_turn_log(self, user_input: str, result) -> None:
        log = TurnLog(
            session_id=result.session_id,
            user_input=user_input,
            final_answer=getattr(result, "final_answer", ""),
            plan=getattr(result, "plan", ""),
            reflection=getattr(result, "reflection", ""),
            trace=list(getattr(result, "trace", [])),
            session_summary=getattr(result, "session_summary", ""),
        )
        log_dir = Path("data/logs")
        safe_timestamp = log.timestamp.replace(":", "-").replace(".", "-")
        log_path = log_dir / f"{result.session_id}-{safe_timestamp}.json"
        log.save_json(log_path)
