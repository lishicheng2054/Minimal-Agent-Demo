# Minimal Agent Demo 中文说明

这是一个从零实现的最小可用 Agent 示例项目。项目目标不是堆功能，而是完整展示一个真实 Agent runtime 的关键闭环：多轮对话、session 维护、工具调用、执行 trace、异常处理、最大步数限制，以及跨轮次继续执行任务。

本项目没有使用 LangChain、OpenHands 等现成 Agent 框架完成主流程。LLM 调用使用 OpenAI 兼容 API，核心 Agent 循环、session 存储、工具注册、工具执行、trace 记录都由项目代码自行实现。

## 项目亮点

- 支持真实 LLM API，可连接 OpenAI，也可配置 DeepSeek 等 OpenAI 兼容接口。
- 支持多轮对话，session 数据会保存到本地 JSON 文件。
- 支持跨轮次任务继续执行，例如第一轮创建 todo，第二轮追问进度时能读到已有任务状态。
- 支持工具调用循环：接收输入、判断是否调用工具、执行工具、读取工具结果、继续推理并输出最终答案。
- 内置 4 个工具：`calculator`、`search`、`todo`、`read_docs`。
- 支持最大步数限制，避免 Agent 陷入无限循环。
- 支持基础异常处理，网络错误、API Key 缺失、工具执行异常都会转成可读信息。
- 支持 trace 执行日志，方便解释 Agent 每一步做了什么。
- CLI 默认像普通聊天一样，只显示最终回复；详细 plan、reflection、trace 会写入 `data/logs/`。
- 提供中文提交文档、录屏脚本、Prompt 与问题解决记录。

## 笔试要求对照

| 要求 | 项目实现 |
| --- | --- |
| 支持多轮对话和 session 维护 | `SessionStore` 将每个 session 保存为 JSON，CLI 支持 `/session` 和 `/new` |
| 不直接依赖现成 Agent 框架 | 未使用 LangChain/OpenHands 主流程，核心 runtime 手写 |
| Agent 基本循环 | `AgentRuntime.run_turn()` 实现 plan、LLM、tool call、tool result、final answer |
| 至少 3 个工具 | 已实现 4 个工具：calculator、search、todo、read_docs |
| 最大步数限制 | `AgentRuntime(max_steps=6)` 默认最多 6 步 |
| 基本异常处理 | `_format_runtime_error()` 与工具层 try/except |
| 工具调用 trace 或执行日志 | `TraceRecorder` 记录每轮事件，CLI 可用 `/trace` 查看 |
| 跨轮次继续执行 | `todo` 状态保存在 session 中，后续轮次可继续读取 |
| 使用真实 LLM API | 通过 OpenAI SDK 调用真实 API，支持 `OPENAI_BASE_URL` |
| README 说明 | 当前文档提供运行方式、系统设计、memory 说明和测试流程 |
| AI Prompt 与问题解决记录 | 见 `docs/prompt_and_notes.md` |

## 目录结构

```text
mini-agent-demo/
  README.md
  pyproject.toml
  .env.example
  docs/
    agent_exam_answer_cn.md
    agent_feature_overview.md
    prompt_and_notes.md
    recording_script.md
    submission_guide_cn.md
  src/minimal_agent_demo/
    __main__.py
    app.py
    cli.py
    config.py
    prompts.py
    runtime.py
    session.py
    trace.py
    tools/
      calculator.py
      read_docs.py
      search.py
      todo.py
  tests/
    conftest.py
    test_cli.py
    test_runtime.py
    test_session.py
    test_tools.py
```

## 环境准备

推荐使用 Python 3.10 或更高版本。

```powershell
cd "C:\Users\lsc15\Desktop\AI agent项目\mini-agent-demo"
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

如果本机没有把 `python` 加入 PATH，也可以使用你机器上的可用 Python 路径执行同样命令。

## 配置 API Key

项目根目录提供了 `.env.example`，请复制为 `.env`：

```powershell
copy .env.example .env
```

OpenAI 配置示例：

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4.1
OPENAI_BASE_URL=
SESSION_DIR=data/sessions
DOCS_ROOT=.
```

DeepSeek 配置示例：

```env
OPENAI_API_KEY=你的-deepseek-api-key
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com
SESSION_DIR=data/sessions
DOCS_ROOT=.
```

注意：`.env` 已经被 `.gitignore` 排除，不会提交到 GitHub。真实 API Key 不应该写进 README、代码或提交历史。

## 启动交互式 CLI

开发模式启动：

```powershell
python -m minimal_agent_demo
```

如果已经安装为命令行脚本，也可以运行：

```powershell
minimal-agent-demo
```

如果使用打包后的可执行文件：

```powershell
.\dist\minimal-agent-demo.exe
```

启动后可以直接输入自然语言：

```text
你：你好
助手：你好，我可以帮你处理代码、文档、计算和任务管理。
```

默认交互模式只展示最终回答，不会把 plan、session summary、reflection、trace 全部刷到屏幕上。这样录屏时更像正常 Agent 对话。详细过程会保存到 `data/logs/`，也可以通过 `/trace` 查看最近一次执行过程。

## CLI 命令

| 命令 | 作用 |
| --- | --- |
| `/help` | 查看帮助 |
| `/session <id>` | 切换到已有 session |
| `/new [id]` | 创建或切换到新 session |
| `/history` | 查看最近对话历史 |
| `/memory` | 查看当前 memory 摘要 |
| `/state` 或 `/context` | 查看当前 session 状态、任务、附件和最近 artifacts |
| `/trace` | 查看最近一次执行 trace |
| `/tools` | 查看已注册工具 |
| `/attach <path>` | 将本地文件摘要加入会话上下文 |
| `/read <path>` | 直接读取本地文档内容 |
| `/exit` | 退出 CLI |

## 单轮命令运行

除了交互式 CLI，也可以用单条命令测试：

```powershell
python -m minimal_agent_demo --session demo --message "帮我创建一个任务：完善 README"
```

开启详细输出：

```powershell
python -m minimal_agent_demo --session demo --message "计算 12 * 7 + 8" --verbose
```

`--verbose` 会在终端显示更完整的 plan、summary、reflection 和 trace 信息，适合调试。日常演示建议保持默认输出。

## 推荐测试流程

下面是一组完整的命令行测试脚本，可以用于录屏或自测。

1. 启动 CLI：

```powershell
python -m minimal_agent_demo
```

2. 测试普通对话：

```text
你好，介绍一下你能做什么
```

3. 测试计算工具：

```text
帮我计算 18 * (7 + 5)
```

4. 测试 mock search 工具：

```text
搜索一下 agent session memory 的相关信息
```

5. 测试 todo 工具和跨轮次状态：

```text
帮我创建一个任务：整理 Agent 项目说明文档
```

然后继续追问：

```text
刚才那个任务现在是什么状态？
```

6. 查看 memory 和 trace：

```text
/memory
/trace
/state
```

7. 测试读取文档：

```text
/read README.md
```

或者让 Agent 自己通过工具读文档：

```text
请读取 README.md，并总结这个项目满足了哪些笔试要求
```

## 自动化测试

运行测试：

```powershell
python -m pytest tests -q
```

在当前开发环境中，也可以使用 Codex 自带 Python 运行：

```powershell
C:\Users\lsc15\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests -q
```

当前测试覆盖内容包括：

- Agent runtime 工具循环
- session 持久化
- 跨轮次 memory 读取
- CLI 命令解析
- 工具函数行为
- OpenAI 兼容 base URL 配置

## 系统设计

核心入口在 `src/minimal_agent_demo/runtime.py`。每一轮对话都由 `AgentRuntime.run_turn()` 驱动。

整体流程如下：

```text
用户输入
  ↓
加载 session
  ↓
写入 user message
  ↓
生成短计划 plan
  ↓
调用 LLM，并暴露工具 schema
  ↓
如果模型请求工具调用，则执行本地工具
  ↓
将工具结果作为 tool message 回传给 LLM
  ↓
重复循环，直到模型给出最终回答或达到最大步数
  ↓
生成 reflection
  ↓
保存 assistant message、plan、reflection、trace
  ↓
返回最终回答
```

这个循环没有交给任何现成 Agent 框架，而是直接用 OpenAI Chat Completions 的 tool calling 能力作为 LLM 接口，工具执行、session 管理、trace 记录都在本地 runtime 中完成。

## 核心模块说明

| 模块 | 职责 |
| --- | --- |
| `app.py` | 命令行入口，解析参数并启动交互式 CLI |
| `cli.py` | 交互式终端、命令解析、聊天输出、日志落盘 |
| `config.py` | 读取 `.env`，创建 OpenAI 兼容客户端 |
| `runtime.py` | Agent 主循环、LLM 调用、工具执行、异常处理 |
| `session.py` | session 状态结构和 JSON 持久化 |
| `trace.py` | 执行 trace 数据结构和日志保存 |
| `prompts.py` | system prompt、plan prompt、reflection prompt |
| `tools/` | 本地工具实现和工具 schema |

## Memory 召回时机与放置方式

本项目的 memory 分为两层。

第一层是结构化 session state，保存在 `data/sessions/<session_id>.json`。它包含最近消息、todo 任务、附件摘要、last plan、last reflection 和 last trace。这是跨轮次继续执行的真实状态来源。

第二层是 prompt 中的 session summary。每一轮对话开始时，runtime 会先加载 session，然后调用 `session.summary()` 生成压缩摘要，并把摘要作为 system message 放进 LLM 输入。这样模型在当前轮推理时能看到之前的任务、消息和状态。

召回发生在每轮 LLM 调用之前：

```text
load session
  ↓
session.summary()
  ↓
build_session_prompt(summary)
  ↓
system message 注入模型上下文
```

为什么这样放置：

- session JSON 是 source of truth，方便稳定保存和调试。
- summary 放入 system prompt，能让模型在每轮开始时理解上下文。
- 最近原始消息也会进入 messages，避免摘要丢失短期细节。
- todo、attachment 等结构化状态不会只依赖模型记忆，而是落盘保存。

## 工具设计

工具通过 schema 注册给模型。模型决定是否调用工具，runtime 负责真正执行工具并把结果回传。

### calculator

用于安全计算基础数学表达式。

示例：

```text
帮我计算 2 + 3 * 4
```

### search

一个 mock search 工具，用于展示搜索工具调用流程。它不会访问真实互联网，而是返回内置的示例搜索结果，适合笔试 demo 和离线录屏。

示例：

```text
搜索 agent memory 的资料
```

### todo

用于创建、更新和查看任务。任务会保存进 session，因此可以跨轮次追问。

示例：

```text
帮我创建一个任务：写项目说明文档
刚才的任务是什么状态？
```

### read_docs

用于读取项目目录下的本地文档。默认根目录由 `DOCS_ROOT` 控制。

示例：

```text
请读取 README.md，并总结运行步骤
```

## Trace 与日志

每一轮对话都会记录 trace 事件，包括：

- `user_input`
- `plan`
- `assistant_draft`
- `tool_call`
- `reflection`
- `final_answer`
- `error`

CLI 默认不会把完整 trace 打印到聊天界面，避免终端输出混乱。详细日志会保存到：

```text
data/logs/
```

查看最近一次 trace：

```text
/trace
```

开启命令行详细输出：

```powershell
python -m minimal_agent_demo --message "计算 8 * 9" --verbose
```

## 跨轮次继续执行示例

第一轮：

```text
帮我创建一个任务：整理 Agent 项目 README
```

Agent 会调用 `todo` 工具创建任务，并把任务保存到当前 session。

第二轮：

```text
刚才那个任务现在是什么状态？
```

Agent 在新一轮开始时加载同一个 session，并从 session summary 中看到已有任务，所以可以基于历史状态回答，而不是把第二轮当成一个完全新的问题。

这就是本项目用于满足“跨轮次继续执行”要求的核心场景。

## 异常处理

项目实现了基础异常处理：

- 未配置 `OPENAI_API_KEY` 时提示用户配置密钥。
- OpenAI 或 DeepSeek 网络连接失败时返回可读错误。
- 工具执行失败时返回 `Tool error: ...`，不会直接中断整个进程。
- LLM 调用失败时会做一次简单重试。
- 达到最大步数时返回无法在步数限制内完成的提示。

## 打包可执行文件

如果要生成 Windows 可执行文件，可以使用 PyInstaller：

```powershell
pip install pyinstaller
pyinstaller --onefile --name minimal-agent-demo src/minimal_agent_demo/__main__.py
```

打包完成后运行：

```powershell
.\dist\minimal-agent-demo.exe
```

注意：可执行文件仍然需要读取 `.env` 或系统环境变量中的 API Key。

## GitHub 与隐私说明

项目已配置 `.gitignore`，会排除：

- `.env`
- `data/`
- `dist/`
- `build/`
- `*.egg-info`
- `__pycache__/`
- `.pytest_cache/`
- 日志文件

请不要把真实 API Key 写入 README、测试文件、截图或录屏画面。若 API Key 曾经暴露，建议立刻在对应平台后台轮换密钥。

## 提交材料入口

本仓库还包含几份中文辅助文档：

- `docs/agent_exam_answer_cn.md`：按笔试题要求整理的说明文档。
- `docs/agent_feature_overview.md`：功能展示和演示说明。
- `docs/submission_guide_cn.md`：提交材料清单。
- `docs/recording_script.md`：终端录屏脚本。
- `docs/prompt_and_notes.md`：AI Prompt 与问题解决记录。

建议提交时提供：

- GitHub 仓库链接
- README 链接
- 录屏文件或录屏链接
- `.env.example`，不要提交真实 `.env`
- 运行测试截图或终端输出

## 当前验证状态

本项目已经通过测试：

```text
23 passed
```

这说明当前版本的 runtime、session、CLI 和工具基础行为都能稳定运行。

