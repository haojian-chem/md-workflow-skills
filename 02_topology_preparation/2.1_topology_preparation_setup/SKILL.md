---
name: topology_preparation_setup
description: 拓扑准备 2.1。当前任务需要进行拓扑准备 setup / routing 时，确认或补充当前体系使用的力场及其它参数定义来源，并把当前任务范围内需要展开的拓扑准备对象落实到 Task Sheet。
---

# 2.1 Topology preparation setup

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 只定义当前 topology-preparation setup 工作项的参数来源核对、处理对象划分以及 Task Sheet 更新规则。

## 目标

当当前任务确实需要进行 topology-preparation setup / routing 时：

- 根据当前体系的正式结构、分类与已确认关系，核对当前拓扑准备实际需要的处理对象；
- 使用当前任务已经明确的力场及其它参数定义来源，或在尚未明确时触发确认；
- 只在当前任务范围内，把需要执行的标准残基拓扑生成、topology-linked 非标准残基参数化、独立非标准参数化和拓扑整合工作落实到 Task Sheet。

本 Skill 不是其它拓扑准备 Step 的强制同任务前置。当前 Task Sheet 如果只覆盖拓扑准备的局部范围，并且对应 Step 已经能够从其它任务的正式结果、当前项目记录、当前对话上下文或用户明确决定获得所需输入，可以直接进入对应 Step，不要求为了形式完整补做 topology-preparation setup。

本 Skill 的规划信息直接写入当前 Task Sheet；不生成额外 setup report 或独立 route 文件。

## 输入与依据

执行当前 setup 工作时至少读取：

- 当前 Task Sheet；
- 当前体系实际使用的正式结构；通常为对应 target 的 `stage1_final.pdb`，也可以是当前任务明确接受的其它正式等价入口；
- 与该结构对应的正式 atom map；
- 当前体系对应的正式 `classification_result.yaml`，用于读取 `STANDARD_RESIDUE`、`TOPOLOGY_LINKED_NONSTANDARD`、`INDEPENDENT_NONSTANDARD`、`SOLVENT_COMPONENT`、`ION_COMPONENT` 及已确认 topology-linked 关系；
- 当前任务、已有项目记录、可追溯执行记录 / 日志、当前对话上下文或用户已经指定的力场及其它参数定义来源。

上述结构、map 和 classification result 可以来自当前 Task Sheet 更早的任务项，也可以来自其它已经完成的任务；本 Skill 不要求这些来源工作必须出现在同一 Task Sheet。

本 Skill沿用已有正式分类，不根据残基名、文件记录类型或当前空间位置重新分类对象。

## 力场与参数定义来源

力场及其它参数定义来源应尽早确认，但“确认当前采用什么”不是本 Skill 的唯一所有权职责。

当前 setup 工作：

1. 先读取当前任务上下文中已经明确的用户决定和正式记录；
2. 已经能够唯一确定当前采用来源时直接使用，不重复询问；
3. 当前 topology-preparation setup 需要这些信息而仍不能唯一确定时，向用户确认；
4. 把本次实际采用、且当前任务范围内需要使用的定义来源路径记录到当前 setup 工作项；
5. 后续具体 Step 在真正需要时仍可按仓库级 Task Execution 规则再次核对，尤其当处理对象、任务范围或用户要求已经变化。

一个体系可以同时使用多个来源。存在多个来源时，对当前任务实际涉及的 `STANDARD_RESIDUE` 检查是否在多个已选来源中重复定义。

若同一 `STANDARD_RESIDUE` 在多个已选来源中都有定义，必须明确当前体系对该残基名实际采用哪个定义来源，并把选择结果与对应路径写入当前 setup 工作项。不存在重复定义时记录已完成检查即可。

`SOLVENT_COMPONENT` 和 `ION_COMPONENT` 是否已有可直接使用的分子拓扑定义，也按本次已经确认的实际参数定义来源判断。

## Reuse

当前 topology-preparation setup 不设置 reuse，也不检索已有 Stage 2 正式结果来决定跳过其它工作项。

当前 Stage 2 的 2.2–2.5 reuse 机制尚未启用；后续 reuse 作为独立更新计划重新设计。

## 确定当前任务范围内的处理对象

只展开**当前 Task Sheet 的任务目标实际覆盖**的拓扑准备工作；不因为当前执行了 setup 就自动把完整 Stage 2 填入 Task Sheet。

当用户要求完整 topology preparation 时，可以按下述分类展开完整所需工作；当当前任务只覆盖其中一部分时，只建立该部分真实需要的工作项和依赖。

### `STANDARD_RESIDUE`

当前任务范围需要生成标准残基 topology，且当前体系存在 `STANDARD_RESIDUE` 时，全部当前处理范围内标准残基共同对应一个标准残基拓扑生成工作项。

本 Skill 只确定该工作项覆盖范围；pdb2gmx 的实际组织与执行属于标准残基拓扑生成 Skill 自身职责。

### `TOPOLOGY_LINKED_NONSTANDARD`

当前任务范围需要 topology-linked 参数化时，根据当前已确认 topology-linked 关系判断哪些非标准残基需要在同一次参数化处理中共同处理。

一个工作项可以覆盖一个或多个 `TOPOLOGY_LINKED_NONSTANDARD` 残基。残基之间存在需要共同处理的拓扑连接，或多个非标准残基与同一标准残基形成需要联合处理的拓扑关系时，可以归入同一个工作项。

除这些稳定关系外，不把“一个非标准残基对应一个工作项”固化为规则；具体组合由执行 Agent 根据当前已确认 topology-linked 关系和实际参数化对象判断。

### `INDEPENDENT_NONSTANDARD`

当前任务范围需要独立非标准参数化时，按残基名建立工作项。同一残基名在当前参数定义语义下使用同一套参数定义，因此同名 `INDEPENDENT_NONSTANDARD` 只建立一个工作项。

若同名残基实际需要不同参数定义，不能在同一残基名下静默建立多套参数；先向用户确认是否需要区分残基名，再继续。

### `SOLVENT_COMPONENT` / `ION_COMPONENT`

当当前任务需要处理这些对象时，检查已经确认的力场 / 参数定义来源是否提供可直接使用的完整分子拓扑定义。

- 已有完整定义：可作为后续拓扑整合的直接输入；
- 缺少完整定义，且当前任务范围包含为其建立参数：按实际 component / 残基名建立独立参数化工作项。

### 拓扑整合

只有当前任务范围包含 topology integration 时才建立或维护拓扑整合工作项。

该工作项显式记录本次整合实际依赖的标准残基拓扑生成、topology-linked 非标准参数化、独立非标准参数化正式结果或工作项，以及能够直接采用的 solvent / ion 拓扑定义。同一类前置结果存在多个时逐项记录，不用任务类型代替具体依赖。

当前任务如果只负责参数化、不负责整合，不因为执行了 topology-preparation setup 自动新增 topology integration。

## 更新 Task Sheet

完成当前 setup 后，只维护当前任务范围实际涉及的内容：

- 在当前 setup 工作项中记录本次实际确认 / 使用的力场及其它参数定义来源；
- 存在多个来源时，记录当前处理范围内 `STANDARD_RESIDUE` 重复定义检查及实际采用来源；
- 为当前任务实际需要的标准残基 topology、topology-linked 参数化、独立非标准参数化或 topology integration 建立 / 调整工作项；
- 工作项的对象和依赖必须能够由当前 Task Sheet 或所引用的既有正式结果唯一定位。

初始 Task Sheet 中仅用于规划占位、但已确认不属于当前任务实际范围的项目，可以在计划更新时删除；已经形成有意义执行历史的任务项按仓库级 Task Execution 规则保留。

Topology validation 不是 Stage 2 的必需环节；是否在当前 Task Sheet 中安排 topology validation，由当前任务范围和用户要求决定，不由本 Skill 强制增加。

完成 Task Sheet 更新后，按仓库级 Task Execution 规则更新当前 setup 工作项状态。

## 结果边界

本 Skill 不生成独立报告，也不向 `project_result_index.md` 登记新的正式结果。

当前工作结果只体现在 Task Sheet 中实际需要保存的：

- 本次核对 / 使用的力场及其它参数定义来源；
- 多来源时的重复定义检查与实际来源选择；
- 当前任务范围内实际展开或调整的拓扑准备工作项、对象和依赖。

后续具体处理的正式结果与登记语义由对应 Skill 自己定义，本 Skill 不复制这些规则。
