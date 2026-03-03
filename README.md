# skill-exec

一个极简的 **skill 执行框架示例**，用于演示如何抽象 skill、注册 skill，并通过统一的执行器调度 skill。

## 核心概念

- **SkillRequest**: 一次调用的输入，包含：
  - `payload`: 业务输入数据（字典）
  - `metadata`: 额外上下文信息（可选，例如 trace_id、用户信息等）
- **SkillResult**: 调用结果，包含：
  - `success`: 是否成功（`True` / `False`）
  - `data`: 成功时返回的数据
  - `error`: 失败时的错误信息
- **Skill**: 抽象基类，所有具体 skill 需要：
  - 继承 `Skill`
  - 实现 `execute(self, request: SkillRequest) -> SkillResult`
- **SkillRegistry**: skill 注册表，用于集中管理所有可用的 skill。
- **SkillExecutor**: 执行器，根据名称从注册表中找到 skill，并负责：
  - 封装输入为 `SkillRequest`
  - 捕获运行期异常并统一转换为 `SkillResult`

## 核心处理流程

1. **定义 skill**

   继承 `Skill`，实现 `execute` 方法，在其中编写具体业务逻辑，并返回 `SkillResult`。

2. **注册 skill**

   将定义好的 skill 实例注册到 `SkillRegistry` 中，使用 `skill.name` 作为唯一标识。

3. **执行 skill**

   通过 `SkillExecutor.execute(name, payload, metadata)` 或 `execute_skill(registry, name, payload, metadata)`：

   - 从注册表中查找名为 `name` 的 skill
   - 构造 `SkillRequest`
   - 调用 `skill.execute(request)`
   - 捕获异常并封装为统一的 `SkillResult`

## 示例

见 `examples.py`，内置了一个简单的 `SumSkill`，实现对两个数字求和。

运行示例：

```bash
python examples.py
```

