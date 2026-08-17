# 网页端多窗口编写协议

Status: CURRENT

本文件描述多个独立网页窗口并行编写不同 Skill 的协作方式。

网页窗口不是运行时 Agent，也不形成新的科学职责层。

## 1. 核心原则

```text
读取范围可以宽
写入所有权必须窄
理解其他 Skill ≠ 获得修改权
```

每个业务窗口应主动读取与当前职责直接相关的其他 Skill，尤其是上下游、相邻边界、输入来源和输出消费者。

这样做是为了：

- 理解 handoff；
- 避免重复定义；
- 发现接口冲突；
- 保证当前 Skill 不越权。

## 2. Main authoring window

主窗口负责共享 authoring / architecture / index 文件，例如：

- `AGENTS.md`；
- `00_authoring/README.md`；
- `00_authoring/AUTHORING_RULES.md`；
- `00_authoring/SYNC_STATUS.md`；
- architecture-freeze records；
- authoring references 和 assets；
- Skill inventory；
- content maps；
- file ownership；
- Manager shared references；
- Tool registry；
- 跨 Skill 接口裁决与最终集成。

## 3. Business Skill window

每个业务窗口只拥有明确 `write_paths`。

开始前至少读取：

- `AGENTS.md`；
- `00_authoring/AUTHORING_RULES.md`；
- `00_authoring/SYNC_STATUS.md`；
- `00_authoring/skill_inventory.yaml`；
- `00_authoring/file_ownership.yaml`；
- 目标 Skill 的 content map；
- 当前目标 Skill；
- 对应 work order（若使用）；
- 与当前 Skill 输入/输出/边界直接相关的其他 Skill / Tool guide。

业务窗口**不应**因为“这些文件不归我写”就拒绝读取相关上下游 Skill。

## 4. Read scope

`read_paths` 不是硬白名单。

如果执行 authoring 时发现需要理解额外 Skill 的接口，可以继续按需读取，即使该文件不在本窗口 `write_paths`。

允许：

```text
读取外部 Skill
→ 理解它提供什么结果/能力
→ 在当前 Skill 中记录接口级依赖
```

不允许：

```text
读取外部 Skill
→ 在当前 Skill 中重新设计它的内部逻辑
```

## 5. Write ownership

没有明确重新分配时，业务窗口只能修改自己的 `write_paths`。

一个文件同一时间只有一个 writer；一个 Skill 目录默认只有一个 writer window。

共享文件不由业务窗口直接修改。

如果用户明确要求当前窗口同时修改另一个 Skill，必须先把对应路径加入当前 write ownership，再实施修改。

## 6. Cross-Skill boundary

在当前 Skill 中，对其他 Skill 只允许定义接口关系：

- 当前 Skill 消费哪个正式结果；
- 当前 Skill 需要外部 Skill 的什么能力；
- 当前 Skill 的结果如何交给下游；
- 依赖哪个已经冻结的外部规则。

禁止把其他 Skill 的以下内容写进当前 Skill：

- 内部执行顺序；
- 默认参数；
- 方法选择规则；
- validation；
- official result 定义；
- 文件保存/索引生命周期；
- 任务计划维护规则。

如果这些外部内容不完整或有冲突，窗口应返回：

```yaml
cross_skill_finding:
  owner_skill:
  issue:
  why_it_matters:
  suggested_change:
```

由 owner window / main window 决定是否修改。

## 7. 不强制 Skill 分类

业务窗口不得因为历史目录存在：

```text
01_workflows/
02_operations/
02_validators/
```

就把新职责机械拆成 Workflow / Operation / Validator。

当前模式是：

```text
main Skill
+ references
+ supporting Skill only for complex, clear boundaries
```

如果当前 main Skill 已经能清楚指导 Agent 完成任务，不为形式完整增加 supporting Skill。

## 8. 不把 Agent 锁进 parser/workflow

业务窗口需要检查：

- 是否把 parser 写成 Agent 理解输入的唯一入口；
- 是否为简单判断增加 schema/dispatcher；
- 是否把推荐 Tool 写成唯一合法实现；
- 是否建立不必要的多层 Skill 调度链。

只有科学/技术方法真正要求时，才规定强制软件/算法/格式路径。

## 9. 写入冲突

- 路径重叠时改为串行；
- 共享接口修改交给 main window；
- 不通过“在自己 Skill 里复制一份外部规则”规避 ownership 冲突；
- 不使用开发子 Agent 解决窗口冲突。

## 10. 交付格式

```yaml
window_id:
task_id:
skill_name:
status: DRAFTED | BLOCKED | REVIEW_REQUIRED
read_context: []
owned_write_paths: []
created_files: []
modified_files: []
validation_run: []
cross_skill_findings: []
tool_requests: []
open_questions: []
summary:
```

交付摘要只说明当前窗口完成的职责和跨 Skill findings，不把其他 Skill 的内部设计重新复制一遍。
