# Prompt and Problem-Solving Notes

## System prompt

```text
You are a compact but real coding agent.

Operating rules:
- First understand the task, then make a short plan, then execute tools if needed.
- Use tools when they help you answer accurately or inspect local context.
- Treat the session summary as persistent memory across turns.
- If the user attached files or asked about the workspace, inspect them before answering.
- After tool use, briefly reflect on the result and make sure the final answer is grounded.
- Keep the final answer concise, useful, and action-oriented.
```

## Tool prompt strategy

- `calculator` is used for arithmetic that should not be guessed.
- `search` is a deterministic mock corpus so the demo is stable offline.
- `todo` stores tasks in session state for cross-turn continuation.
- `read_docs` lets the agent inspect local files from the demo workspace.

## Memory placement

- Raw messages are stored in the session JSON file.
- A compact session summary is injected into the system prompt before each turn.
- The latest plan, reflection, attachments, and trace are also stored in the session so `/state` and `/trace` can explain continuity.
- Tool output is appended back into the same session so later turns can refer to it.

## Problem solving record

1. The first version of the code relied on missing imports and placeholder methods.
2. I converted the session layer to immutable-style updates so each change returns a new session object.
3. I implemented a safe arithmetic parser instead of using `eval`.
4. I used a mock search corpus to keep the demo deterministic and offline-friendly.
5. I made the `todo` tool update session state so a later turn can ask about progress.
6. I added trace events so each tool step is visible in the final result.
7. I extended the session model to persist the last plan, last reflection, and latest trace.
8. I adjusted tests after the second-turn session scenario needed a third fake model response.

## Verification result

- Unit tests passed: `20 passed`
- The runtime loop, tools, session persistence, CLI commands, and artifact display are covered by tests.
- The CLI now prints readable plan / final answer / reflection / trace output for recording and demo purposes.
