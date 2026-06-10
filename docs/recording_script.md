# 录屏脚本

这是一个适合录屏时直接照着走的终端演示脚本。当前版本已经升级成命令式交互终端，体验更接近 Claude Code。默认终端只显示最终回答，计划、反思和 trace 会落到 `data/logs/`。

## 录屏前准备

1. 将 `.env.example` 复制为 `.env`。
2. 配置 `OPENAI_API_KEY`。
3. 安装依赖。
4. 如果想从头演示，先清空 session 目录。

## 演示流程

### 场景 1：进入交互式工作台

运行：

```bash
python -m minimal_agent_demo
```

先输入：

```text
/help
```

讲解重点：

- 这是一个命令式终端工作台，而不是一次性脚本。
- 可以用 `/session`、`/new`、`/history`、`/memory`、`/trace`、`/tools`、`/attach`、`/read` 管理上下文。
- 还可以用 `/state` 或 `/context` 直接看当前会话摘要、最近消息、最近计划和最近反思。
- 先展示工作台，再进入对话，更像真实的终端 Agent 工具。

### 场景 2：第一轮，展示计划 + 工具调用 + 反思

运行：

```bash
python -m minimal_agent_demo --session demo --message "What is 2 + 3 * 4?"
```

讲解重点：

- 先生成短计划，再执行工具。
- Agent 会判断需要使用 `calculator` 工具。
- trace 里能看到计划、工具调用、反思和最终答案。
- 这一步展示完整闭环：输入 -> 计划 -> 工具 -> 反思 -> 回答。

### 场景 3：跨轮次续跑

运行：

```bash
python -m minimal_agent_demo --session demo --message "Create a task to write the README."
```

然后再运行：

```bash
python -m minimal_agent_demo --session demo --message "How is the task going?"
```

讲解重点：

- 第二轮使用的是同一个 `session id`。
- 第一轮创建的任务会从 session state 里被召回。
- Agent 会继续处理上一轮留下的任务，而不是把第二个问题当成全新问题。
- `/state` 会显示当前任务、最近计划和最近反思，方便现场解释“记忆放在哪里”。

### 场景 4：读取文档

运行：

```bash
python -m minimal_agent_demo --session demo --message "Read the README and summarize the system design."
```

讲解重点：

- `read_docs` 工具可以读取本地文档。
- 这展示了除了数学和任务状态以外的另一个非平凡工具路径。
- 也可以先执行 `/attach README.md`，再让模型基于附加内容回答问题。

## 建议口播

1. “这是一个手写的 Agent runtime，不是对现成框架的简单包装。”
2. “这个终端界面支持命令、历史、memory、trace 和 session 切换，比较接近 Claude Code 的工作方式。”
3. “Agent 会把 session state 持久化到磁盘，所以可以跨轮次继续任务。”
4. “工具调用是显式的、可追踪的，而且有最大步数限制。”
5. “记忆会通过 session summary、任务状态、附件和最近 trace 一起被召回。”
6. “这些工具都尽量保持小而稳定，方便演示和理解。”
7. “`/state` 命令可以直接看当前会话的摘要、最近计划和最近反思，像一个轻量工作台。”
