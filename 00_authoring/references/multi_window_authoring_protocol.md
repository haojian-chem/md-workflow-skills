# 网页端多窗口编写协议

Status: CURRENT

本文件描述多个独立网页窗口并行编写不同 Skill 的协作方式。

网页窗口不是运行时 Agent，也不形成新的科学职责层。

## 1. 核心原则

```text
读取范围可以宽
写入所有权必须窄
理解其他 Skill ≠ 获得修改权或定义权
```

每个业务窗口应主动读取与当前职责直接相关的其他 Skill，尤其是上下游、相邻边界、输入来源和输出消费者。

读取的目的只有：

- 理解 handoff；
- 避免重复定义；
- 发现接口冲突；
- 保证当前 Skill 不越权。

## 2. 新窗口启动

业务 Skill authoring 窗口默认启动链：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

随后只按当前任务需要继续读取：

- 目标 content map；
- 对应 architecture freeze；
- 直接相关的上下游/相邻 Skill；
- 当前需要的 Tool guide / reference；
- 涉及多窗口写入协调时再读取 `file_ownership.yaml`；
- 涉及当前 inventory/status 时再读取 `skill_inventory.yaml` / `SYNC_STATUS.md`。

不要把整个 `00_authoring/` 作为每个新窗口的固定 preload。

## 3. Main authoring window

主窗口负责共享 authoring / architecture / index 文件，包括：

- `AGENTS.md`；
- `00_authoring/SKILL.md`；
- `00_authoring/README.md`；
- `00_authoring/references/`；
- `00_authoring/assets/`；
- `00_authoring/scripts/`；
- `00_authoring/architecture_freezes/`；
- authoring inventory / content maps / file ownership；
- Manager shared references；
- Tool registry；
- 跨 Skill 接口裁决与最终集成。

## 4. Business Skill window

每个业务窗口只拥有明确 `write_paths`。

业务窗口**不应**因为“这些文件不归我写”就拒绝读取相关上下游 Skill。

但没有明确重新分配时，只修改自己的 `write_paths`。

一个文件同一时间只有一个 writer；一个 Skill 目录默认只有一个 writer window。

如果用户明确要求当前窗口同时修改另一个 Skill，必须先把对应路径加入当前 write ownership，再实施修改。

## 5. Read scope

`read_paths` 不是硬白名单。

允许：

```text
读取外部 Skill
→ 理解它提供什么结果 / 能力
→ 在当前 Skill 中记录接口级依赖
```

不允许：

```text
读取外部 Skill
→ 在当前 Skill 中重新设计它的内部逻辑
```

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

对任何准备加入当前 Skill 的规则，都必须应用：

`content_ownership_and_deduplication.md`

原则是：**当前 Skill 只定义自己如何做；对其他 Skill 只定义自己需要什么。** 已有 owner 的外部规则只引用，不复制、改写或总结成可独立执行的第二份规范。

如果外部内容不完整或有冲突，窗口应返回：

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

## 10. 交付前去重检查

交付前至少确认：

- 当前 Skill 没有写其他环节“应该怎么做”；
- 没有复制或改写另一个 owner 的规则；
- 没有形成以后需要多处同步修改的 shadow specification；
- 外部内容已经尽量缩成 `consume / require / handoff`。

任一项不满足时，先处理 ownership / deduplication，再交付。

## 11. 交付格式

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
