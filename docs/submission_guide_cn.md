# Minimal Agent Demo 提交说明

## 1. 项目简介

本项目是一个从零实现的最小可用 Agent Demo，目标是展示一个完整、可交互、可续跑、可打包的 Agent 主流程，而不是简单套用现成 Agent 框架。

核心流程如下：

`接收用户输入 -> 生成计划 -> 工具调用 -> 读取工具结果 -> 反思 -> 输出最终回复`

项目支持：

- 多轮对话
- session 记忆
- 任务状态持续
- 工具调用 trace
- 本地文档读取
- 真实 LLM API 调用
- 可执行文件打包

---

## 2. 功能展示

### 2.1 直接聊天

启动后可以直接输入普通文本和 Agent 对话，例如：

```text
你好
```

终端默认只显示最终回复，更像正常聊天，不会把内部计划过程全部刷出来。

### 2.2 命令式工作台

支持这些命令：

- `/help`：查看帮助
- `/session <id>`：切换会话
- `/new [id]`：新建会话
- `/history`：查看最近消息
- `/state`：查看当前会话状态
- `/trace`：查看最近一次执行 trace
- `/tools`：查看可用工具
- `/memory`：查看当前 memory 摘要
- `/attach <path>`：附加本地文件上下文
- `/read <path>`：读取本地文件
- `/exit`：退出

### 2.3 工具能力

当前内置 4 个工具：

- `calculator`：安全计算表达式
- `search`：mock 搜索，用于演示检索能力
- `todo`：创建、查看、更新任务，支持跨轮次执行
- `read_docs`：读取本地文档

### 2.4 跨轮次继续执行

示例：

第一轮：

```text
Create a task to write the README.
```

第二轮：

```text
How is the task going?
```

Agent 会读取同一个 session 中的任务状态，继续处理，而不是把第二轮当成全新问题。

### 2.5 详细过程落盘

默认终端只展示最终回复，计划、反思和 trace 会写入：

```text
data/logs/
```

如果需要看完整过程，可以使用：

```bash
dist\minimal-agent-demo.exe --verbose
```

或者直接查看日志文件。

---

## 3. 环境配置

### 3.1 复制环境文件

项目根目录已经提供：

- `.env.example`

如果没有 `.env`，先复制一份：

```powershell
Copy-Item .env.example .env
```

### 3.2 DeepSeek 配置

如果你要使用 DeepSeek，请把 `.env` 配成这样：

```env
OPENAI_API_KEY=你的DeepSeekKey
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-pro
SESSION_DIR=data/sessions
DOCS_ROOT=.
```

说明：

- `OPENAI_API_KEY`：填你自己的 DeepSeek API Key
- `OPENAI_BASE_URL`：DeepSeek 官方兼容接口地址
- `OPENAI_MODEL`：DeepSeek 模型名

如果是普通 OpenAI，也可以改成对应的 base url 和 model。

---

## 4. 启动方式

### 4.1 运行可执行文件

```powershell
cd "C:\Users\lsc15\Desktop\AI agent项目\mini-agent-demo"
dist\minimal-agent-demo.exe
```

### 4.2 运行源码

```powershell
cd "C:\Users\lsc15\Desktop\AI agent项目\mini-agent-demo"
python -m minimal_agent_demo
```

---

## 5. 推荐演示流程

### 流程 1：先看命令

输入：

```text
/help
```

展示点：

- 这个项目不是一次性脚本
- 它是一个可交互终端工作台

### 流程 2：普通对话

输入：

```text
你好
```

展示点：

- 终端只显示最终回复
- 像正常聊天一样

### 流程 3：任务跨轮次

输入：

```text
Create a task to write the README.
```

再输入：

```text
How is the task going?
```

展示点：

- 同一个 session 会继续记住任务
- Agent 可以基于已有状态回答

### 流程 4：查看状态与 trace

输入：

```text
/state
```

再输入：

```text
/trace
```

展示点：

- session 里保存了什么
- Agent 这轮做了哪些步骤

---

## 6. 怎么验证成果

### 6.1 运行测试

```powershell
C:\Users\lsc15\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests -q
```

### 6.2 验证 exe

```powershell
dist\minimal-agent-demo.exe --message /help
dist\minimal-agent-demo.exe --message 你好
```

### 6.3 查看日志

```text
data/logs/
```

---

## 7. 常见问题

### 7.1 只看到连接失败

检查：

- `.env` 里的 `OPENAI_API_KEY`
- `.env` 里的 `OPENAI_BASE_URL`
- `.env` 里的 `OPENAI_MODEL`
- 网络是否可以访问对应接口

### 7.2 看不到完整过程

这是正常的，因为默认就是聊天式输出。  
如果要看完整过程：

- 用 `--verbose`
- 或查看 `data/logs/`
- 或执行 `/trace`

### 7.3 想重置会话

删除：

```text
data/sessions/
```

即可重新开始一个干净会话。

---

## 8. 提交说明

建议提交时附上这些内容：

- 代码链接
- 运行方式
- 系统设计
- memory 召回时机与放置方式说明
- Prompt 与问题解决记录
- 录屏或终端演示

---

## 9. 一句话总结

这是一个能直接运行、能直接聊天、能跨轮次续跑、能查看日志、能打包成 exe 的最小可用 Agent Demo。
