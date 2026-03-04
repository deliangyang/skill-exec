# skill-exec

一个极简的 **skill 执行框架示例**，用于演示如何抽象 skill、注册 skill，并通过统一的执行器调度 skill，支持同步 / 异步 skill 以及简单工作流组合。

## 核心概念

- **SkillRequest**: 一次调用的输入，包含：
  - `payload`: 业务输入数据（字典）
  - `metadata`: 额外上下文信息（可选，例如 trace_id、用户信息等）
- **SkillResult**: 调用结果，包含：
  - `success`: 是否成功（`True` / `False`）
  - `data`: 成功时返回的数据
  - `error`: 失败时的错误信息
  - `code`: 业务状态码，例如 `"OK"` / `"VALIDATION_ERROR"` / `"EXECUTION_ERROR"` 等
- **Skill**: 抽象基类，所有具体 skill 需要：
  - 继承 `Skill`
  - 实现 `execute(self, request: SkillRequest) -> SkillResult`
- **SkillRegistry**: skill 注册表，用于集中管理所有可用的 skill。
- **SkillExecutor**: 执行器，根据名称从注册表中找到 skill，并负责：
  - 封装输入为 `SkillRequest`
  - 支持 `execute` 返回协程的 **异步 skill**（内部使用 `asyncio.run` 执行）
  - 捕获运行期异常并统一转换为 `SkillResult`（并设置 `code` 字段）
- **SequentialWorkflowSkill**: 顺序工作流 skill，内部按顺序调用多个已注册的 skill：
  - 输入：使用请求的 `payload` 作为初始上下文
  - 每个 step 若返回 `dict`，会 merge 回上下文，供后续 step 使用
  - 输出：包含最终上下文和每个 step 的执行结果列表

## 核心处理流程

1. **定义 skill**

   继承 `Skill`，实现 `execute` 方法，在其中编写具体业务逻辑，并返回 `SkillResult`。

2. **注册 skill**

   将定义好的 skill 实例注册到 `SkillRegistry` 中，使用 `skill.name` 作为唯一标识。

3. **执行 skill**

   通过 `SkillExecutor.execute(name, payload, metadata)` 或 `execute_skill(registry, name, payload, metadata)`：

   - 从注册表中查找名为 `name` 的 skill
   - 构造 `SkillRequest`
   - 调用 `skill.execute(request)`（支持返回协程）
   - 捕获异常并封装为统一的 `SkillResult`，并根据异常类型设置 `code`

4. **组合工作流（可选）**

   使用 `SequentialWorkflowSkill` 将多个已有 skill 串在一起形成一个简单工作流，例如：

   - `sum`：对 `a + b` 求和，返回 `{"result": ...}`
   - `wait`：异步等待一段时间，返回 `{"slept": ...}`
   - `sum_then_wait`：先执行 `sum`，再执行 `wait`，共享同一个 `payload` 上下文

## 示例

见下列文件中的示例：

- `examples.py`:
  - `SumSkill`: 对两个数字求和
  - `WaitSkill`: 使用 `asyncio.sleep` 的异步 skill
  - `SequentialWorkflowSkill("sum_then_wait", ["sum", "wait"], ...)`: 简单顺序工作流
- `llm_agent.py`:
  - 演示如何把 skill 暴露为「工具」，并由（模拟的）LLM 选择调用哪个 skill 以及入参
- `orchestrator.py`:
  - 演示一个极简自研任务编排器如何基于 `SkillExecutor` 串联多个 skill
- `llm_agent_openai.py`:
  - 演示如何使用 OpenAI 官方 SDK 的 tools（function calling）能力，将 skill 作为工具暴露给真实 LLM
- `orchestrator_prefect.py`:
  - 演示如何在 Prefect flow 中，以 DAG 方式编排多个 skill

运行示例：

```bash
# 基础示例（同步 / 异步 skill + 内置工作流）
python examples.py

# 模拟 LLM 工具调用
python llm_agent.py

# 极简自研任务编排示例
python orchestrator.py

# OpenAI LLM function calling 集成示例（需要 OPENAI_API_KEY）
python llm_agent_openai.py

# Prefect 任务编排集成示例
python orchestrator_prefect.py
```

