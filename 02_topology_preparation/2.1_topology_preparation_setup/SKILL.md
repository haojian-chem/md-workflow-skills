---
name: topology_preparation_setup
description: 拓扑准备 2.1。为后续 2.2–2.5 建立适用于当前体系的拓扑准备拆分方案，确认当前方案使用的力场及其它参数定义来源，并记录各处理对象、实际 source target lineage 与后续归属。
---

# 2.1 Topology preparation setup

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 只定义当前 topology-preparation setup 的参数来源核对、处理对象拆分和后续工作方案。

## 目标

2.1 是 2.2–2.5 的 setup prerequisite。

在任何 2.2–2.5 工作开始前，都必须已经存在一个**适用于当前体系、当前处理范围和当前参数定义基础**的已完成 2.1 拆分方案。

该 2.1 可以：

- 位于当前 Task Sheet；
- 位于同一科研任务的前序 Task Sheet，并由当前 Task Sheet 明确定位。

因此，不要求每一张后续 Task Sheet 都重复建立 2.1；但不能因为更换 Task Sheet 而绕过 2.1 本身。

2.1 负责形成：

- 当前拓扑准备方案实际采用的力场及其它参数定义来源；
- 当前体系进入 Stage 2 时实际对应的 source target record(s)；
- 当前体系中需要进入 2.2、2.3、2.4、2.5 的处理对象及拆分关系；
- topology-linked 非标准参数化对象如何分组；
- independent nonstandard / solvent / ion 对象如何进入参数化或直接整合；
- 2.5 需要汇合的前置工作集合。

2.1 不执行 pdb2gmx、量化参数化、拓扑整合或 topology validation，也不为尚未真正实例化的未来 2.2–2.5 targets 预先创建 target records。

## 输入与依据

执行当前 setup 时至少需要：

- 当前 Task Sheet；
- 当前体系实际采用的正式结构，通常为某个 Stage 1 final target 的 `stage1_final.pdb`；
- 与该结构对应的正式 atom map；
- 该 atom map 的 `target_record` 指向的实际 upstream target record；
- 当前体系对应的正式 `classification_result.yaml`；
- 当前科研任务中可追溯的用户决定，以及相关前序 Task Sheet、已有正式项目记录、可追溯执行记录 / 日志、当前对话上下文中已经明确的力场及其它参数定义来源。

上述结构、map、target record 和 classification result 可以来自当前 Task Sheet，也可以来自前序 Task Sheet / 已有正式结果；2.1 不要求这些上游工作必须与自己写在同一张 Task Sheet。

如果当前 Stage 2 setup 同时处理多个实际 upstream target branches，逐项记录各自 target record；不得通过上游 `target_id` 相同/不同判断它们是否属于同一 branch。

2.1 沿用正式分类，不根据残基名、文件记录类型或当前空间位置重新分类对象。

## Target lineage planning boundary

2.1 是 setup / decomposition owner，不是后续 target-record producer。

因此：

- 2.1 记录当前已存在的 upstream `target_record` 完整路径；
- 对每个计划中的 2.2 / 2.3 / 2.4 processing object，记录它基于哪些**当前已存在 upstream target records**以及它依赖哪些其它计划对象；
- 不为尚未执行的 2.2 / 2.3 / 2.4 / 2.5 编造未来 `targets/target_xxx.yaml` 路径；
- 真正进入 2.2–2.5 时，由对应 Skill 为实际 local target 创建 current target record，并把当时真实存在且实际参与当前对象形成的 target records 写入 `source_target_records`；
- 2.5 的合流 target source 不能仅依据 2.1 的类别名推断，必须在实际整合时使用真正被消费的 2.2 / 2.3 / 2.4 / direct-source target records。

## 力场与参数定义来源

2.1 负责把**当前拆分方案实际采用的**力场和其它参数定义来源确认并记录下来。

处理方式：

1. 先读取当前可追溯上下文中已经明确的用户决定和正式记录；
2. 已经能够唯一确定当前方案采用的来源时直接使用，不重复询问；
3. 当前 setup 需要该信息而仍不能唯一确定时，向用户确认；
4. 把本次实际采用、且会影响当前 Stage 2 处理方案的来源记录到 2.1 工作项；
5. 后续 2.2–2.5 在真正执行时可以再次核对这些来源；如果后续确认得到的新信息会使当前 2.1 拆分方案失效，则先更新 / 重新形成适用的 2.1 方案，再继续后续 Step。

一个体系可以同时使用多个来源。

存在多个来源时，对当前体系实际涉及的 `STANDARD_RESIDUE` 检查是否在多个已选来源中重复定义；若重复，必须明确当前方案实际采用哪个定义来源。

`SOLVENT_COMPONENT` 和 `ION_COMPONENT` 是否已有可直接用于整合的完整分子拓扑定义，也按当前已确认来源判断。

## Reuse

当前 2.1 不设置 reuse。

如果同一科研任务的前序 Task Sheet 已经完成一个仍适用于当前体系 / 当前处理范围的 2.1，后续 Task Sheet 可以**消费该既有 prerequisite**，而不是把这种前置依赖解释成当前 2.1 的 reuse 机制。

如果处理对象、分类、target lineage、拓扑关系或参数定义基础已经变化并使原拆分方案不再适用，则必须重新进入 2.1 形成新的方案。

## 处理对象拆分

### `STANDARD_RESIDUE`

当前体系存在需要生成标准残基 topology 的 `STANDARD_RESIDUE` 时，将当前处理范围内的全部标准残基归入一个 2.2 处理对象。

2.1 为该对象记录实际 upstream Stage 1 target record(s) 与处理范围。2.2 真正执行时再建立 2.2 local target record。

2.1 只确定该对象范围；pdb2gmx 的 chain handling、实际命令和输出组织属于 2.2 自身职责。

### `TOPOLOGY_LINKED_NONSTANDARD`

根据当前已确认 topology-linked 关系，确定需要共同参数化的非标准残基组合。

一个 2.3 处理对象可以包含一个或多个 `TOPOLOGY_LINKED_NONSTANDARD` 残基。存在需要共同处理的拓扑连接，或多个非标准残基与同一标准残基形成需要联合处理的拓扑关系时，可以归入同一个对象。

2.1 记录该对象实际来源的 Stage 1 target record(s)，以及如果参数化模型需要标准残基全原子片段时对相应 2.2 processing object 的依赖。此时 2.2 尚未执行则只记录**计划对象依赖**，不伪造未来 2.2 target record 路径。

不把“一个非标准残基固定对应一个 2.3”作为规则；具体组合由当前已确认关系和实际参数化对象决定。

### `INDEPENDENT_NONSTANDARD`

按残基名建立 2.4 处理对象。

同一残基名在当前参数定义语义下使用同一套参数；若同名实例实际需要不同参数定义，不能在同一残基名下静默建立多套参数，先向用户确认是否需要区分残基名。

2.1 记录当前 2.4 object 所属的实际 upstream Stage 1 target record(s)；2.4 真正执行时再为 local target 创建正式 target record。

### `SOLVENT_COMPONENT` / `ION_COMPONENT`

检查当前已确认的参数定义来源是否提供可直接用于 2.5 的完整分子拓扑定义：

- 已有完整定义：作为 2.5 的直接输入，并保留其实际 upstream target record 来源，不建立对应 2.4 参数化对象；
- 缺少完整定义：按实际 component / 残基名建立对应 2.4 处理对象，并记录 upstream target record(s)。

### 2.5 整合对象

为当前体系形成 topology integration 方案，明确本次整合需要汇合的：

- 标准残基 topology 处理对象；
- topology-linked 非标准参数化处理对象；
- independent nonstandard 参数化处理对象；
- 可直接采用的 solvent / ion topology 定义及其 upstream target 来源。

同一类存在多个前置对象时逐项记录，不以处理类别代替具体对象。

2.1 只定义输入集合和对象关系，不定义 2.5 内部整合方法，也不预先创建 2.5 target record。实际 2.5 target 的 `source_target_records` 由真正完成并被当前整合消费的 target records 决定。

## Task Sheet 记录

2.1 本身不生成独立 setup report。

当前 2.1 工作项必须记录足以让后续 Task Sheet 恢复拆分方案的信息，包括：

- 当前 Stage 2 输入体系实际 upstream target record(s) 的完整绝对路径；
- 本次采用的力场及其它参数定义来源；
- 多来源时的重复定义检查及实际采用来源；
- 当前体系的 2.2 / 2.3 / 2.4 处理对象；
- 各处理对象当前已知的 upstream target record(s)；
- 处理对象之间的真实依赖，例如某个 2.3 object 需要对应 2.2 object 提供标准残基全原子结构；
- 可直接进入 2.5 的 solvent / ion 对象、定义来源与 upstream target record；
- 2.5 的前置对象集合。

如果后续 2.2–2.5 工作与 2.1 位于同一 Task Sheet，可以直接把相应工作项展开到当前计划中。

如果为了上下文隔离或执行拆分，后续工作放到新的 Task Sheet，则不要求在当前 Task Sheet 中保留全部未来执行项；新的 Task Sheet 必须能够定位当前已完成 2.1 工作项，并据此恢复自己所需的处理对象和依赖。

2.6 不属于 2.1 的强制后续工作；是否安排 topology validation 由对应 Task Sheet 的实际范围决定。

## Completion

当前 2.1 可以标记 `已完成` 的条件是：

- 当前体系和处理范围能够唯一定位；
- 当前 Stage 2 输入所对应 upstream target record(s) 已明确；
- 当前拆分方案所需的力场及参数定义来源已经明确；
- 2.2–2.5 的处理对象 / 直接输入 / 依赖关系已经闭合到足以支持后续执行；
- 当前 Task Sheet 已记录可追溯的拆分方案来源和结果；
- 没有为尚未真正实例化的未来 targets 伪造 target record 路径。

2.1 不向 `project_result_index.md` 登记独立正式结果；它的正式前置作用由记录该方案的 Task Sheet 工作项承担。
