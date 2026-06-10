SYSTEM_PROMPT = """You are a compact but real coding agent.

Operating rules:
- First understand the task, then make a short plan, then execute tools if needed.
- Use tools when they help you answer accurately or inspect local context.
- Treat the session summary as persistent memory across turns.
- If the user attached files or asked about the workspace, inspect them before answering.
- After tool use, briefly reflect on the result and make sure the final answer is grounded.
- Keep the final answer concise, useful, and action-oriented.
"""


def build_session_prompt(session_summary: str) -> str:
    return (
        "Current session summary:\n"
        f"{session_summary}\n\n"
        "Use this summary to continue previously started work and preserve task state across turns."
    )


def build_plan_prompt(user_input: str, attachments_summary: str = "") -> str:
    return (
        "Create a short execution plan for the user's request.\n"
        "Include the objective, any likely tools, and the next step.\n\n"
        f"User request:\n{user_input}\n\n"
        f"Attachments:\n{attachments_summary or 'None'}"
    )


def build_reflection_prompt(draft_answer: str, tool_summary: str = "") -> str:
    return (
        "Check the draft answer against the tool results and session state.\n"
        "If the answer is solid, return a short confirmation. If not, mention what needs fixing.\n\n"
        f"Draft answer:\n{draft_answer}\n\n"
        f"Tool summary:\n{tool_summary or 'None'}"
    )
