---
name: md-workflow-tool-authoring
description: 为本项目设计、实现、测试、注册、升级或废弃确定性共享 Tool 时使用。Tool 提供精确、稳定、可测试的确定性能力；它不是 Agent 理解任务的 parser gate，也不替代 main Skill 的科学判断。
---

# Purpose

把真正适合程序化的确定性动作实现为受控共享 Tool，同时保持：

```text
Agent 理解任务和科学判断
→ current main Skill

deterministic parsing / transform / calculation / write / mechanical validation
→ Tool
```

Tool 不是新的科学决策层，也不是 runtime orchestration 层。

# Startup

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 00_authoring/md-workflow-tool-authoring/SKILL.md
→ 按需 00_authoring/references/deterministic_tool_protocol.md
→ tools/tool_registry.yaml
```

按需再读取目标 Tool、实际 caller Skill、`evals/` evidence 和多窗口 coordination。

涉及旧 Tool/runtime 迁移时才读取：

```text
legacy/tools/
legacy/contracts/
legacy/runtime/
```

先恢复：

```text
已做过
已否定
仍未验证
```

# 1. 是否真的需要 Tool

优先 Tool 化：精确 parsing / extraction、hash / mapping、稳定变换、批量处理、可重复数值计算、格式校验、安全写入、高频重复确定性动作。

不足以开发 Tool：包装一次简单读取、强迫 Agent 经过 parser、为了减少几行 Skill guidance、为了恢复旧 route/event/state/transaction runtime。

必须明确定位：

```text
required_capability
preferred_implementation
optional_helper
```

# 2. Tool 不承担

Tool 不得：

- 解释用户开放式科研意图；
- 扩大 Task 目标；
- 决定其它 Skill 行为；
- 作开放式科学判断；
- 向用户提问或创建 Agent；
- 作为理解原始科研文件的唯一 parser gate；
- 为 ordinary Lightweight Runtime 构造 Workstream/route/event/transaction；
- 修改未授权路径。

# 3. Current Tool package

Current shared Tool root：

```text
tools/<tool-name>/
├── tool.yaml
├── <entrypoint>
├── tests/          # only when package-local tests are useful
└── README.md       # only when useful
```

跨 repository-level acceptance / fixtures / benchmark：

```text
evals/<tool-name>/
```

Current registry：

```text
tools/tool_registry.yaml
```

不再使用 `05_tools/` / `04_evals/` 等会与 Stage 5 / Stage 4 混淆的编号根目录。

# 4. Interface

优先：

```text
明确文件 / 目录
+ 必要参数
→ deterministic action
→ 明确输出 / report
```

不要设计成 runtime task object 解包全局项目状态后再决定下一阶段。

建议按实际复杂度记录：

```yaml
name:
version:
status: DESIGNED | IMPLEMENTED | TESTED | ACTIVE | DEPRECATED | RETIRED
capability:
role: required_capability | preferred_implementation | optional_helper
callers: []
entrypoint:
inputs: []
outputs: []
read_paths: []
write_paths: []
side_effects: []
compatibility:
```

只在真正有价值时增加 cache、transactional write 或 structured error 字段。

# 5. Permissions / side effects

写入型 Tool 必须明确：输入、输出位置、覆盖策略、冲突行为、部分失败 cleanup 和执行前后 validation。

Tool 不越过 caller Skill 授权自行管理其它科研职责。Stage-specific index maintenance 等例外必须由对应 Stage Skill 明确授权。

# 6. Testing

测试根据真实风险选择正常输入、错误输入、边界值、权限越界、重复运行、部分失败、输出 validation、performance 或 compatibility。

不要求所有 Tool 继承 Legacy FAST/FULL runtime-schema validation 模式。

# 7. Registry / activation

只有实现完成并通过适用测试后，才可在 `tools/tool_registry.yaml` 标记为 `ACTIVE`。

Registry 至少应能定位 name/version/status、Tool path/entrypoint、capability/role、主要 caller、重要 read/write scope、tests/evidence，以及 replacement/deprecation 信息（如有）。

# 8. Legacy Tool migration

旧 `05_tools/` 已整体迁移到：

```text
legacy/tools/
```

这些工具中的许多依赖旧 contracts/runtime。重新成为 current Tool 必须逐个完成：

```text
确认仍有 current capability 价值
→ 移除 Legacy runtime coupling
→ 建立 explicit Lightweight interface
→ current tests / validation
→ 迁入 tools/
→ current registry reactivation
```

不得整批因为历史 ACTIVE 状态恢复。

# 9. Caller ownership

Tool authoring 可以读取 caller Skills 以理解 capability，但不得在 Tool 中重新定义 caller 的科研目标、方法选择、reuse、project result registration 或用户确认逻辑。

# 10. Delivery check

- [ ] Tool 化确有确定性价值；
- [ ] Tool 不是 parser gate；
- [ ] required/preferred/optional 定位清楚；
- [ ] 不承担开放式科研判断；
- [ ] write scope 明确；
- [ ] tests 覆盖真实风险；
- [ ] current Tool 写入 `tools/`，evidence 写入 `evals/`；
- [ ] Legacy tool 只从 `legacy/tools/` 按单个 capability 迁移；
- [ ] 未恢复 Legacy orchestration。
