# Minimal Agent Demo

A small, from-scratch agent demo that uses the OpenAI API directly, without depending on an existing agent framework.
It now includes an interactive terminal UI with commands, session switching, history, memory, trace inspection, and file reading.

## What it shows

- Multi-turn conversation with session persistence
- A hand-written agent loop: user input -> plan -> tool execution -> reflection -> final answer
- At least 4 tools:
  - `calculator`
  - `search` (mock)
  - `todo`
  - `read_docs`
- Max step limit
- Basic exception handling
- Tool trace logging
- Stored plan/reflection artifacts for each turn
- Cross-turn continuation through saved session state
- Interactive terminal UI with Claude Code style commands
- Default terminal output shows only the final answer; detailed plan/trace/reflection are saved to `data/logs/`

## Project layout

```text
mini-agent-demo/
  pyproject.toml
  .env.example
  README.md
  src/minimal_agent_demo/
    app.py
    config.py
    prompts.py
    runtime.py
    session.py
    trace.py
    tools/
      calculator.py
      search.py
      todo.py
      read_docs.py
  tests/
    test_runtime.py
    test_cli.py
```

## Setup

1. Create a virtual environment.
2. Install the package in editable mode.
3. Copy `.env.example` to `.env`.
4. Set your OpenAI key.

Example:

```bash
cd mini-agent-demo
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

If you are using the bundled Codex Python runtime, you can run the tests with:

```bash
C:\Users\lsc15\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests -q
```

## Environment variables

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1
OPENAI_BASE_URL=
SESSION_DIR=data/sessions
DOCS_ROOT=.
```

## Run the demo

Interactive mode:

```bash
python -m minimal_agent_demo
```

Useful commands:

```text
/help
/session demo-2
/new demo-2
/history
/memory
/state
/trace
/tools
/attach README.md
/read README.md
/exit
```

Single-turn mode:

```bash
python -m minimal_agent_demo --session demo --message "Create a task to write the README."
```

## System design

The core runtime lives in `src/minimal_agent_demo/runtime.py`. It owns the loop:

1. Load the session from JSON
2. Build a prompt from the current session summary and recent messages
3. Ask the model for a short plan
4. Call the OpenAI Chat Completions API with registered tools
5. If the model returns tool calls, execute them locally
6. Feed tool outputs back into the model
7. Ask the model for a short reflection
8. Store plan, reflection, and trace artifacts back into the session
9. Stop when the model produces a final answer or the max step limit is reached

Session state lives in `src/minimal_agent_demo/session.py` and is saved as JSON under `SESSION_DIR`.
The session contains recent messages plus task state, attachments, the last plan, the last reflection, and the latest trace.
That is what lets the agent continue work across turns and answer progress checks without starting from scratch.

## Memory recall

Memory is recalled in two places:

1. Before each turn, the runtime loads the full session and adds a compact summary into the system prompt.
2. The raw message history is also included so the model can see immediate prior context.

The summary acts as a compressed memory layer when the conversation gets longer.
The raw session state is the source of truth for cross-turn task continuation.

## Trace logging

Each turn writes trace events in memory and returns them in the result:

- user input
- plan
- assistant draft
- tool call
- reflection
- final answer

This is enough to explain why the agent took each step during the demo.

## Cross-turn continuation example

Turn 1:

```text
Create a task to write the README.
```

Turn 2:

```text
How is the task going?
```

Because the task is stored in session state, the second turn can answer from prior state instead of treating the prompt as a brand-new problem.

## CLI behavior

The terminal UX is command-driven and stateful:

- Plain text goes through the agent loop
- `/state` shows the current session summary, recent messages, last plan, and last reflection
- `/trace` shows the latest execution trace from the saved session state
- `/attach <path>` adds a local file summary into the session memory
- `/read <path>` reads a local file immediately

This makes the demo easier to record on screen and closer to a lightweight coding workspace.

## Testing

Run the test suite:

```bash
C:\Users\lsc15\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests -q
```

## Notes for the submission

- The demo uses the official OpenAI SDK directly.
- The agent runtime is handwritten.
- The session and trace layers are custom.
- The tool loop is explicit and observable.
- Recording script: `docs/recording_script.md`
- The CLI is interactive and command-driven, closer to a lightweight terminal agent workspace.
- `/state` and `/context` show the current session summary plus recent messages.
- 功能说明文档：`docs/agent_feature_overview.md`
- 提交说明文档：`docs/submission_guide_cn.md`
- 笔试题说明文档：`docs/agent_exam_answer_cn.md`
