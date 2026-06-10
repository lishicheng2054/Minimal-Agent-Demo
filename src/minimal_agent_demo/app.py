from __future__ import annotations

import argparse

from minimal_agent_demo.cli import InteractiveCLI, is_command
from minimal_agent_demo.config import load_settings, make_client
from minimal_agent_demo.runtime import AgentRuntime


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the minimal agent demo")
    parser.add_argument("--session", default="demo", help="Session id to resume")
    parser.add_argument("--message", help="Single user message; if omitted, enter interactive mode")
    parser.add_argument("--verbose", action="store_true", help="Show detailed plan/trace output in terminal")
    args = parser.parse_args()

    settings = load_settings()
    runtime = AgentRuntime(None, settings)
    cli = InteractiveCLI(runtime, session_id=args.session, verbose=args.verbose)

    if args.message:
        if is_command(args.message):
            print(cli.run_command(args.message))
        else:
            print(cli.submit_message(args.message))
        return

    print("Minimal Agent Demo")
    print("输入普通文本开始对话，/help 查看命令，/exit 退出。")
    if not settings.api_key:
        print("提示：当前未检测到 OPENAI_API_KEY。可以先测试命令，真正对话前需要配置密钥。")
    while True:
        message = input("你> ").strip()
        if not message:
            continue
        if is_command(message):
            print(cli.run_command(message))
            if cli.should_exit:
                break
            continue
        if message.lower() in {"exit", "quit"}:
            break
        try:
            print(f"助手: {cli.submit_message(message)}")
        except RuntimeError as exc:
            print(f"助手: 发生错误，{exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"助手: 发生错误，{exc}")
