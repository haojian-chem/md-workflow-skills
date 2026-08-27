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

- 理解直接接口与上下游正式结果关系；
- 避免重复定义；
- 发现接口冲突；
- 保证当前 Skill 不越权。

## 2. 新窗口启动

业务 Skill authoring 窗口的正式 authoring 链从本项目 authoring Skill 开始：

```text
00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

测试或运行环境中的 `AGENTS.md` 如果存在，只属于 Skill 体系外的调用入口辅助；它不是本协议的 startup/read dependency，也不能作为 writer、authority、Skill dependency 或规则可达性的依据。

随后只按当前任务需要继续读取：

- 对应 architecture freeze；
- 直接相关的上下游/相邻 Skill；
- 当前需要的 Tool guide / reference；
- 涉及多窗口 writer 协调时再读取 `00_authoring/coordination/file_ownership.yaml` 或对应 window work order；
- 涉及 Stage catalog / 建设状态时读 `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`；
- 涉及跨 Stage runtime architecture 时再读取 `00_authoring/project_design/lightweight_runtime_v2_spec.md`。

**如果当前任务是正式 Skill generation、freeze 建立/替换或 implementation milestone 更新，读取 Master Plan 不是可选项，而是状态同步前置。**

不要把整个 `00_authoring/` 作为每个新窗口的固定 preload。

## 3. Main authoring window

主窗口负责共享 authoring / architecture / coordination 文件，包括：

- `00_authoring/SKILL.md`；
- `00_authoring/README.md`；
- `00_authoring/references/`；
- `00_authoring/assets/`；
- `00_authoring/scripts/`；
- `00_authoring/architecture_freezes/`；
- `00_authoring/project_design/`；
- `00_authoring/coordination/`；
- Manager shared references；
- Tool registry；
- 跨 Skill 接口裁决与最终集成。

如测试环境需要维护外部 `AGENTS.md`，可由主窗口协调该辅助文件，但这不改变它位于 Skill 体系之外、且不属于 authoring dependency 的边界。

不再通过每个 Skill 一份 content map 或一个全局 skill inventory 来授予/判断写入权。

`MD_WORKFLOW_MASTER_PLAN.md` 通常仍是共享文件，但针对**当前 Skill authoring 直接造成的状态变化**存在一个窄的 status-only 写例外，见第 9 节。

## 4. Business Skill window

每个业务窗口只拥有明确 `write_paths`。

业务窗口**不应**因为“这些文件不归我写”就拒绝读取相关上下游 Skill。

但没有明确重新分配时，只修改自己的 `write_paths`，以及第 9 节定义的 status-only 共享写例外。

一个文件同一时间只有一个 writer；一个 Skill 目录默认只有一个 writer window。

如果用户明确要求当前窗口同时修改另一个 Skill，必须先明确扩展当前 write ownership，再实施修改。

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

在当前 Skill 中，对其他 Skill 只允许定义当前职责真实需要的接口关系：

- 当前 Skill 消费哪个正式结果；
- 当前 Skill 需要外部 Skill 的什么能力；
- 依赖哪个已经冻结的外部规则。

普通相邻 Step 的流程关系由拥有该关系的 Stage main Skill 表达；下游怎样解释和消费当前结果，由下游 Skill 自己的 Object requirements / input contract 定义。当前 Skill 不因为存在下游而另外定义 handoff 规则或 handoff 文件。

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

如果外部内容不完整或有冲突，窗口返回简短 finding 即可：

```text
owner_skill:
issue:
why_it_matters:
suggested_change:
```

不要求先转换成固定 schema。由 owner window / main window 决定是否修改。

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

已确定的 Stage / Step package 目录可以提前保留；目录存在不代表内部 `SKILL.md` 已获批生成。

## 8. 不把 Agent 锁进 parser/workflow

业务窗口需要检查：

- 是否把 parser 写成 Agent 理解输入的唯一入口；
- 是否为简单判断增加 schema/dispatcher；
- 是否把推荐 Tool 写成唯一合法实现；
- 是否建立不必要的多层 Skill 调度链。

只有科学/技术方法真正要求时，才规定强制软件/算法/格式路径。

## 9. 写入冲突与状态同步例外

一般规则：

- 路径重叠时改为串行；
- 共享科学/架构接口修改交给 main window；
- 不通过“在自己 Skill 里复制一份外部规则”规避 ownership 冲突；
- 不使用开发子 Agent 解决窗口冲突。

需要显式登记 writer 时，才在：

`00_authoring/coordination/file_ownership.yaml`

增加 assignment。

### 9.1 Master Plan status-only 共享写

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 是 Stage / Step 建设状态和 current entry 的唯一 owner。为避免 Skill 完成后状态长期陈旧，完成当前 Skill / freeze 的窗口必须承担状态同步责任。

写入前：

```text
refetch current main
→ 读取 MD_WORKFLOW_MASTER_PLAN.md
→ 读取 coordination/file_ownership.yaml
→ 检查是否存在该共享文件的显式 writer
```

若不存在显式冲突，当前窗口可以只修改：

- 自己负责的 Stage / Step 建设状态；
- 该 Step 的 current `SKILL.md` / freeze entry；
- 因本次生成直接导致的 Stage 汇总状态文字。

不得借此修改其他 Stage 的 catalog、科学规则或 architecture。

若已有显式 writer，则不并发修改；当前窗口必须向该 writer 给出精确状态 patch / handoff，并在交付中明确状态尚待落地。**不能因为共享文件不归当前业务窗口就完全忽略状态维护。**

## 10. 交付前去重与状态检查

交付前至少确认：

- 当前 Skill 没有写其他环节“应该怎么做”；
- 没有复制或改写另一个 owner 的规则；
- 没有形成以后需要多处同步修改的 shadow specification；
- 外部内容已经尽量缩成当前职责真实需要的 `consume / require`；
- 若本次改变了 Skill/freeze/validation 建设状态，Master Plan 已同步，或已有明确 writer handoff；
- 若 Stage main Skill 维护该 Step 的 current/freeze-only entry，该入口已同步。

任一项不满足时，先处理 ownership / deduplication / status synchronization，再交付。

## 11. 交付

交付只需要说明：

```text
当前窗口负责什么
修改了哪些 owned paths
做了什么 validation
状态 owner 是否已同步
有哪些 cross-skill findings
还有哪些未决问题
```

不要求统一交付 YAML，也不要把其他 Skill 的内部设计重新复制一遍。
