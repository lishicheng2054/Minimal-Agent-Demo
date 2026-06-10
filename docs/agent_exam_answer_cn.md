# 从零实现一个最小可用 Agent - 笔试题说明文档

## 1. 项目概述

本项目实现了一个从零编写的最小可用 Agent Demo，用于满足“从零实现一个最小可用 Agent”的笔试要求。

项目特点：

- 不直接依赖现成 Agent 框架
- 核心 runtime 自己实现
- 使用真实 LLM API
- 支持多轮对话和 session 维护
- 支持工具调用、trace、日志、跨轮次任务续跑
- 可打包成 exe 并直接演示

核心主流程如下：

`接收用户输入 -> 判断是否需要工具 -> 执行工具 -> 读取工具结果 -> 继续推理 -> 输出最终答案`

---

## 2. 题目要求对应说明

### 2.1 支持多轮对话和 session 维护

实现方式：

- 每个会话有独立 `session_id`
- session 内容会落盘保存到 `data/sessions/`
- 记录内容包括：
  - 最近消息
  - tasks
  - attachments
  - last_plan
  - last_reflection
  - last_trace

效果：

- 用户第二轮输入时，Agent 可以继续读取上一轮的状态
- 不会把每一轮都当成全新问题

---

### 2.2 不直接依赖现成 Agent 框架

实现方式：

- 没有使用 LangChain、OpenHands 等框架去包主流程
- runtime 逻辑由 `src/minimal_agent_demo/runtime.py` 自己实现
- 自己维护：
  - prompt 组装
  - 工具 schema
  - LLM 调用
  - 工具执行循环
  - reflection
  - session 存储

---

### 2.3 核心 runtime 需要自己实现

实现方式：

- `AgentRuntime` 负责整个 Agent 主循环
- `run_turn()` 实现完整对话轮次
- `TraceRecorder` 负责记录执行 trace
- `SessionState` 负责 session 记忆与任务状态

---

### 2.4 至少支持一个基本循环

实现方式：

1. 接收用户输入
2. 先生成 plan
3. 判断是否需要调用工具
4. 如果需要则执行工具
5. 读取工具结果
6. 继续下一步推理
7. 直到模型给出最终答案

日志中可查看：

- user_input
- plan
- assistant_draft
- tool_call
- reflection
- final_answer

---

### 2.5 至少提供 3 个工具

当前提供 4 个工具：

- `calculator`
  - 安全计算表达式
- `search`
  - mock 搜索，稳定可演示
- `todo`
  - 创建/查看/更新任务
- `read_docs`
  - 读取本地文档

满足题目要求的同时，也支持跨轮次任务状态演示。

---

### 2.6 最大步数限制

实现方式：

- `AgentRuntime` 中设置 `max_steps`
- 防止工具调用陷入死循环
- 超过最大步数会给出结束提示

---

### 2.7 基本异常处理

实现方式：

- 对 OpenAI API 调用进行异常捕获
- 对网络错误进行友好提示
- 对工具执行异常进行返回包装
- 终端不会直接抛出未处理堆栈给用户

---

### 2.8 工具调用 trace 或执行日志

实现方式：

- `TraceRecorder` 保存完整执行过程
- 每轮对话结果写入 `data/logs/`
- 终端默认只展示最终回复
- 详细过程可通过 `/trace` 或日志文件查看

日志内容包括：

- 用户输入
- 计划
- 工具调用
- 工具输出
- 反思
- 最终答案

---

### 2.9 跨轮次继续执行场景

场景示例：

第一轮：

```text
Create a task to write the README.
```

第二轮：

```text
How is the task going?
```

实现效果：

- 第一轮创建任务并写入 session
- 第二轮可以直接基于 session 里的任务状态继续回答
- 这说明 Agent 不是每次都重新开始，而是能延续之前的工作

---

### 2.10 需要使用真实的 LLM API

实现方式：

- 直接使用 OpenAI Python SDK
- 支持 `OPENAI_API_KEY`
- 支持 `OPENAI_BASE_URL`
- 支持 DeepSeek 这类 OpenAI 兼容接口

示例 `.env`：

```env
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-pro
SESSION_DIR=data/sessions
DOCS_ROOT=.
```

---

## 3. 运行方式

### 3.1 安装

```powershell
cd "C:\Users\lsc15\Desktop\AI agent项目\mini-agent-demo"
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

### 3.2 运行源码

```powershell
python -m minimal_agent_demo
```

### 3.3 运行打包 exe

```powershell
dist\minimal-agent-demo.exe
```

---

## 4. 交互说明

### 4.1 默认聊天模式

直接输入普通文本即可对话，例如：

```text
你好
```

终端默认只展示最终回复，不显示 plan、trace 等内部细节。

### 4.2 命令模式

可用命令：

- `/help`
- `/session <id>`
- `/new [id]`
- `/history`
- `/trace`
- `/tools`
- `/memory`
- `/state`
- `/attach <path>`
- `/read <path>`
- `/exit`

---

## 5. System Design

### 5.1 核心 runtime

文件：

- `src/minimal_agent_demo/runtime.py`

职责：

- 组装提示词
- 调用 LLM
- 判断是否需要工具
- 执行工具
- 读取工具结果
- 继续循环
- 生成最终答案

### 5.2 Session 与 memory

文件：

- `src/minimal_agent_demo/session.py`

职责：

- 保存消息历史
- 保存任务状态
- 保存附件
- 保存最近 plan
- 保存最近 reflection
- 保存最近 trace

### 5.3 Trace 与日志

文件：

- `src/minimal_agent_demo/trace.py`

职责：

- 保存每轮执行事件
- 落盘为 JSON 日志

### 5.4 CLI

文件：

- `src/minimal_agent_demo/cli.py`
- `src/minimal_agent_demo/app.py`

职责：

- 提供交互终端
- 提供命令
- 默认显示聊天式输出
- 详细过程写入日志

---

## 6. Memory 的召回时机与放置方式

### 6.1 召回时机

在每一轮用户输入开始时：

- 读取 session
- 构造 summary
- 把 summary 放入 system prompt

### 6.2 放置方式

memory 分两层：

1. **原始消息历史**
   - 作为 session 的完整上下文
2. **压缩摘要**
   - 作为 system prompt 的 memory 记忆层

这样既能保留完整对话，又能在长对话时维持高效上下文。

---

## 7. 终端操作录屏建议

录屏时可以按这个顺序展示：

1. 启动程序
2. 输入 `/help`
3. 输入普通文本 `你好`
4. 输入一个会触发工具调用的问题
5. 输入创建任务指令
6. 再问一次进度，展示跨轮次记忆
7. 输入 `/state`
8. 输入 `/trace`

---

## 8. 提交内容清单

按题目要求，建议提交这些内容：

- 代码链接
- 终端或网页操作录屏
- README
- 系统设计说明
- memory 召回时机与放置方式说明
- AI Prompt 与问题解决记录

---

## 9. AI Prompt 与问题解决记录

建议说明：

- 项目如何从零搭建
- 如何实现 runtime 循环
- 如何设计 tools
- 如何处理 session 持久化
- 如何让 CLI 更像聊天
- 如何把 plan / reflection / trace 落盘
- 如何支持 DeepSeek / OpenAI 兼容接口

---

## 10. 一句话总结

这是一个从零实现、支持多轮对话、具备工具调用、支持 trace、可落盘记忆、可打包运行的最小可用 Agent Demo。
