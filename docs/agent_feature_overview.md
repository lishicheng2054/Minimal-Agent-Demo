# Minimal Agent Demo 功能说明

## 1. 项目简介

这是一个从零实现的最小可用 Agent Demo，核心目标不是“套一个现成 Agent 框架”，而是自己实现一条完整的 Agent 主流程：

`接收用户输入 -> 生成计划 -> 调用工具 -> 读取工具结果 -> 反思 -> 输出最终答案`

项目使用真实的 OpenAI API，支持多轮对话、session 记忆、工具调用 trace、任务状态维护，并提供一个类似 Claude Code 的中文命令行交互界面。

---

## 2. 这个 Demo 能展示什么

### 2.1 真实 LLM 调用

- 使用 OpenAI Python SDK 直接调用真实模型
- 不是假对话，也不是硬编码回复
- 支持通过 `.env` 或环境变量配置 `OPENAI_API_KEY`

### 2.2 多轮对话和 session 维护

- 每个会话有独立的 `session_id`
- 之前的消息、任务、附件、计划、反思、trace 都会保存到本地 JSON
- 下一轮输入时，Agent 会读取同一个 session，继续处理之前的上下文

### 2.3 自研 Agent 主循环

Demo 内部不是简单的一问一答，而是一个显式循环：

1. 读取用户输入
2. 先让模型生成简短 plan
3. 如果需要，调用工具
4. 读取工具返回结果
5. 让模型基于结果继续推理
6. 输出最终答案
7. 再生成一段 reflection

### 2.4 工具系统

当前提供 4 个工具：

- `calculator`：安全计算四则运算和简单表达式
- `search`：mock 搜索，用来演示检索型工具
- `todo`：创建、查看、更新任务，支持跨轮次继续执行
- `read_docs`：读取本地文档内容

### 2.5 命令行工作台

这个项目不是普通脚本，而是一个可交互的终端工作台，支持这些命令：

- `/help`：查看命令说明
- `/session <id>`：切换到已有会话
- `/new [id]`：新建或切换会话
- `/history`：查看最近消息
- `/trace`：查看最近一次执行 trace
- `/tools`：查看可用工具
- `/memory`：查看当前 memory 摘要
- `/state`：查看当前会话状态
- `/attach <path>`：把本地文件附加到会话上下文
- `/read <path>`：直接读取本地文件
- `/exit`：退出程序

### 2.6 可展示的 trace 和状态

每次对话都会记录：

- 用户输入
- plan
- assistant draft
- tool call
- reflection
- final answer

同时 session 里会保存：

- 最近消息
- 任务列表
- 附件摘要
- 最近 plan
- 最近 reflection
- 最近 trace

这让你在演示时可以很清楚地说明“Agent 是怎么一步步做决策的”。

### 2.7 最大步数限制和异常处理

- Agent 有最大步数限制，避免无限循环
- 工具执行和网络调用都有基本异常处理
- 当 OpenAI API key 缺失或网络错误时，会给出中文友好提示

---

## 3. 典型演示场景

### 场景 1：先看工作台

启动：

```powershell
dist\minimal-agent-demo.exe
```

然后输入：

```text
/help
```

你可以展示：

- 这个终端支持命令
- 不是一次性脚本
- 可以切换会话、查看历史、查看 trace 和 state

### 场景 2：数学工具调用

输入：

```text
What is 2 + 3 * 4?
```

你可以展示：

- Agent 会先生成 plan
- 然后调用 `calculator`
- 再读取工具结果
- 最后输出答案和 reflection

### 场景 3：跨轮次任务继续执行

第一轮：

```text
Create a task to write the README.
```

第二轮：

```text
How is the task going?
```

你可以展示：

- 第一轮会创建任务并保存到 session
- 第二轮会读取同一 session
- Agent 能基于已有任务状态继续回答，不会把第二轮当成全新问题

### 场景 4：读取本地文档

输入：

```text
Read the README and summarize the system design.
```

你可以展示：

- `read_docs` 工具可以读取本地文件
- Agent 能把文档内容加入推理流程
- 这体现了 Agent 的“查资料 -> 总结 -> 回答”能力

### 场景 5：附件上下文

先执行：

```text
/attach README.md
```

再提问：

```text
Please summarize the project features.
```

你可以展示：

- 附件会进入 session 上下文
- 后续提问可以基于附件继续回答

---

## 4. 为什么它算一个完整的 Agent

这个 Demo 不是“工具函数合集”，而是具备完整 Agent 的核心要素：

- 有输入
- 有记忆
- 有计划
- 有工具选择
- 有工具执行
- 有结果回读
- 有反思
- 有跨轮次持续状态
- 有 trace
- 有最大步数限制

这意味着它已经具备“能思考、能行动、能继续”的最小闭环。

---

## 5. 运行方式

### 安装依赖

```powershell
cd "C:\Users\lsc15\Desktop\AI agent项目\mini-agent-demo"
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

### 配置环境变量

`.env` 示例：

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1
SESSION_DIR=data/sessions
DOCS_ROOT=.
```

### 启动交互终端

```powershell
dist\minimal-agent-demo.exe
```

或者：

```powershell
python -m minimal_agent_demo
```

---

## 6. 验证方式

### 运行测试

```powershell
C:\Users\lsc15\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests -q
```

### 验证打包后的可执行文件

```powershell
dist\minimal-agent-demo.exe --message /help
dist\minimal-agent-demo.exe --session demo --message "What is 2 + 3 * 4?"
```

---

## 7. 相关文件

- 主运行时：`src/minimal_agent_demo/runtime.py`
- 命令行界面：`src/minimal_agent_demo/cli.py`
- 会话与记忆：`src/minimal_agent_demo/session.py`
- 提示词模板：`src/minimal_agent_demo/prompts.py`
- 工具实现：`src/minimal_agent_demo/tools/`
- 录屏脚本：`docs/recording_script.md`
- 问题记录：`docs/prompt_and_notes.md`

---

## 8. 一句话总结

这是一个“从零实现、可交互、可续跑、可追踪、可打包”的最小可用 Agent Demo，适合展示 Agent 的核心工作流，而不是只展示几个零散功能。
