---
name: topology_integration_and_assembly
description: Lightweight Runtime v2 的 2.5 Topology integration and assembly。将 2.2 standard topology、2.3 topo-linked nonstandard unit、2.4 independent nonstandard、以及当前 Task Sheet 中 2.1 已记录可直接使用的 solvent/ion definitions 整合成 final all-atom topology package；负责 final atom ordering/index、final moleculetype 组织、linked-site modification、charge replacement、bonded-term migration、parameter-definition 汇总和 final topology/coordinate/map assembly，但不替代 2.6 topology validation，也不重新执行 2.3 parameterization。
---

# 目标

将 Stage 2 上游已经生成或确认的 topology/parameterization 结果组装成一个确定、完整、可交给 2.6 验证的 final topology package。

核心目标：

```text
2.2 standard
+
2.3 topo-linked nonstandard unit(s)
+
2.4 independent nonstandard
+
FF-direct solvent / ion definitions
↓
final topology package
```

2.5 负责“组装完成”，2.6 负责“验证组装结果是否正确、完整且可被 GROMACS 接受”。

# Lightweight Runtime 接口

## Purpose

完成 topology integration and assembly，并产生 deterministic topology package 与 2.5 integration report。

## Object requirements

当前 Task Sheet 的 2.5 `对象` 必须能够明确定位本体系实际需要的上游正式结果，不得靠扫描整个项目猜测输入。

至少需要：

- 当前 Task Sheet 中 2.1 已记录的力场及其它参数定义来源、2.5 处理对象与直接输入；
- 2.2 standard-only structure、topology、molecule `.itp`、map；
- 每个 2.3 topo-linked nonstandard **unit** 的 parameterization result、map、linked-site modification information；
- 2.4 independent nonstandard type-level topology 与当前体系实例 structure/map；
- 当前 Task Sheet 中 2.1 已记录可以直接引用的 solvent/ion topology definitions；
- Workflow 1 最终结构整理/映射结果中已经确定的 chain identity / chain assignment；
- 当前体系信息中已经确认的 expected charge / composition 等 2.5 所需体系事实。

2.5 读取 2.3 输出时必须以 `nonstandard unit` 为处理对象。一个 unit 可以包含多个 nonstandard residues；不得假设一个 2.3 result 只对应一个 residue。

2.5 不重新给 topo-linked unit 分 chain。若 unit 的 standard-side linked residues 全部属于同一条 standard chain，则其 chain assignment 应已由 Workflow 1 确定为该 chain；若跨多条 standard chains，则应由 Workflow 1 为该 unit 建立独立 chain identity。2.5 可因 covalent topology 把多个 chain 组织进同一 GROMACS `moleculetype`，但不得覆盖既有 chain identity。

不要求读取 2.2/2.3/2.4 的全部执行历史，只消费其正式 handoff 结果。

## Reuse conditions

已有 2.5 正式结果只有在以下条件都明确等价时才可自动复用：

1. 2.2 standard topology/structure/map 输入相同；
2. 所有实际参与的 2.3 nonstandard unit 结果及 linked-site modification information 相同；
3. 所有实际参与的 2.4 type/instance 结果相同；
4. 2.1 已记录的力场及其它参数定义来源与实际引用 force-field include tree 相同；
5. final system composition、chain assignment 与 covalent connectivity 组织相同；
6. expected charge 等影响 assembly 的体系信息相同；
7. `nrexcl`、`[ exclusions ]`、attachment-site atom type、parameter conflict 等用户决定相同；
8. 用户没有明确要求重新整合或做对照。

任一条件明确变化时重新执行 2.5。信息不足无法判断等价时，由 Task Execution Agent 向用户确认。

直接复用时引用已有 final topology package，不复制一套新文件，也不创建当前任务空目录。

## Execution rules

详细 molecule-level integration 规则仅在实际开始 topology migration/assembly 时读取：

`references/topology_integration_rules.md`

详细六类 parameter-definition 汇总、两轮 dedup 与 conflict 规则仅在处理 parameter-level definitions 时读取：

`references/parameter_definition_deduplication.md`

主执行顺序：

1. 解析并固定本次 2.5 输入集合；
2. 根据已确认 covalent connectivity 与上游 chain assignment 决定 final `moleculetype` 组织，同时保留 chain identity；
3. 按 coordinate ownership 确定 final atom set：标准部分来自 2.2 并应用全部 confirmed standard-side deletions；topo-linked 只纳入 unit 自身最终 SOURCE + ADDED_H atoms；independent 使用 2.4 all-instance structure；FF-direct 组件使用当前体系实际实例；
4. 以 Workflow 1 heavy-atom identity/order 为结构骨架，结合 2.2/2.3/2.4 all-atom order，建立 final all-atom order；
5. 在 topology integration 开始前同时冻结 canonical final atom index、`final_system.map` 与所有 source/local atom → final atom index mapping；
6. 以第 5 步 final index 为唯一目标编号，对每个 final `moleculetype` 执行 molecule-level topology integration：建立 final `[ atoms ]`，执行 standard-side deletion cleanup、attachment-site atom-type review、charge modification/replacement，并迁移 bonded terms、`[ pairs ]`、`[ exclusions ]` 与其它 molecule-level directives；每个 final moleculetype 的 local `.itp` 在本步骤直接生成；
7. 汇总 2.2–2.4 中六类 parameter-level definitions，内部 dedup 后再与实际 force-field include tree dedup/conflict processing，生成一个 consolidated parameter-definition `.itp`；
8. 组装 `final_system.top`：按 include order 引用 base force-field definitions、consolidated parameter-definition `.itp`、第 6 步生成的 final molecule `.itp`、FF-direct solvent/ion topology，并写入 `[ system ]` / `[ molecules ]`；
9. 严格按第 4–5 步已经冻结的 final all-atom order 写出 `final_system.gro`；不得重新生成另一套 atom order 或 map；
10. 执行 2.5 assembly completeness gate，确认 final topology / coordinates / map 使用同一 canonical final index；
11. 写 `topology_integration_report.yaml` 并交给 2.6。

### Final moleculetype 组织

自动组织以 **covalent connectivity** 为准，不以原始 chain 边界为准：

```text
unit 只共价连接一个现有 moleculetype
→ unit 并入该 moleculetype

unit 同时共价连接多个现有 moleculetype
→ 这些 standard components + unit 合并成一个 final moleculetype
```

chain identity / residue identity 继续保留；改变的是 GROMACS `moleculetype` 组织。

不得把真正的 covalent topology 拆成多个 moleculetype 后再依赖 `[ intermolecular_interactions ]` 拼接。

若 topology-linked relation 不是已确认的 covalent connectivity，且其 final moleculetype 组织不能从上游正式信息确定，当前 Step 向用户确认，不自行扩展规则。

### Final all-atom order 与 canonical final index

final all-atom order **必须先于 molecule-level topology integration 冻结**。

规则：

- Workflow 1 只提供 heavy-atom identity/order 骨架；
- standard residue 内部继承 2.2 all-atom order minus confirmed deletions；
- topo-linked unit 只保留 unit 自身 final SOURCE + ADDED_H atoms，并保持 2.3 相对顺序；
- independent instances 继承 2.4 all-instance order；
- linked nonstandard block 不按 attachment site 紧邻插入 standard residue，而在所属 standard residue block 后按上游 object order 组织；
- 只做 final moleculetype organization 所需的块级组合，不自由重排。

final all-atom order 冻结时必须同步生成：

```text
canonical final atom index
final_system.map
source/local atom → final atom index mapping
```

后续 final molecule `.itp` 与 `final_system.gro` 都消费这同一套 index；不得在 topology integration 或 coordinate writing 时建立第二套编号。

### Multiple-unit overlap

若 2.5 发现两个名义上不同的 nonstandard units 在 standard-side modification、attachment、deletion 或 charge modification 上出现实质重叠：

- 不自动 merge 两套 2.3 结果；
- 暂停对应 integration；
- 向用户确认；
- 默认建议将其作为一个 unit 重新由 2.3 处理。

2.5 不负责补救错误的 2.3 unit 划分。

## Validation requirements

2.5 自身只执行 **assembly completeness gate**，不替代 2.6。

只有以下条件全部成立，2.5 才可标记为 `已完成`：

- final `moleculetype` 组织已经确定；
- final all-atom order、canonical final atom index 与 final map 已在 topology integration 前冻结；
- 所有 standard / topo-linked / independent / FF-direct components 已归入 final atom set / final topology package；
- 每个 final moleculetype 的 local `.itp` 已按 canonical final index 完成；
- standard-side deletion mechanical cleanup 已完成；
- molecule-level directives 已按本 Skill 规则迁移；
- 六类 parameter-definition 已汇总并完成两轮 dedup/conflict processing；
- `final_system.top` 已完整引用所需 definitions / molecule topology，并写入 `[ system ]` / `[ molecules ]`；
- `final_system.gro` 与 `final_system.map` 使用同一 canonical final atom order/index；
- final topology 中不存在对 deleted atom、CAP 或其它 non-final atom 的引用；
- 所有需要用户决定的项目已经解决；
- `topology_integration_report.yaml` 中 unresolved decisions/conflicts 为空。

以下检查属于 2.6，不作为 2.5 的替代完成条件：

- `gmx grompp` 是否通过；
- missing parameter / atom type coverage；
- 1–4 / exclusion 完整性验证；
- charge/connectivity 科学 sanity；
- topology ↔ coordinate 逐原子完整验证；
- GROMACS warning/error 判读。

## Official results

当前任务实际执行新的 2.5 时，正式结果至少包括：

```text
final_system.top
final_system.gro
final_system.map
all final local molecule .itp files
one consolidated parameter-definition .itp
topology_integration_report.yaml
```

其中 dedicated parameter-definition `.itp` 必须单独存在，统一包含从 2.2–2.4 收集的：

```text
[ atomtypes ]
[ bondtypes ]
[ angletypes ]
[ dihedraltypes ]
[ pairtypes ]
[ nonbond_params ]
```

具体 local molecule `.itp` basename 与 consolidated parameter-definition `.itp` basename 由当前 Workflow 2 文件命名约定决定；2.5 不把六类 directive 拆成六个文件。

`topology_integration_report.yaml` 必须列出完整 final package file set，使 2.6 无需扫描目录猜测依赖。

# 职责边界

负责：

- 消费 Workflow 1 已确定 chain assignment，不重新分 chain；
- final atom set / all-atom order / canonical final index；
- final moleculetype assembly；
- final `[ atoms ]` 与 numbering；
- standard-side deletion application；
- attachment-site standard atom-type applicability review；
- linked-region charge modification；
- molecule-level directive migration；
- parameter-level definition collection/dedup/conflict handling；
- final coordinates / map / top / local itp assembly；
- 2.5 completeness gate 与 integration report。

不负责：

- 重新做 2.3 parameterization；
- 重新定义 nonstandard unit；
- 重新决定 topo-linked unit 的 chain assignment；
- 根据 atom/residue name 猜跨步骤 identity；
- 自动发明 replacement atom type；
- 处理 unresolved chemistry without user decision；
- 通过 `[ intermolecular_interactions ]` 规避 covalently connected components 的 moleculetype merge；
- 用 `grompp success` 代替 2.6；
- 自动修复 2.6 发现的 topology 科学问题；
- 创建 Legacy route / Workstream / event / runtime task-result。

# 工作目录

2.5 使用 Task Sheet 为当前任务记录的 task-scoped 2.5 工作目录：

```text
<2.5_base_work_directory>/<task_id>/
```

Workflow 2 的稳定 base directory 尚未由当前 shared planning catalog 正式落地前，本 Operation 不自行改写 shared planning 文件或假定另一套目录名。

Task Execution Agent 必须先做 reuse；只有确实需要执行新的 2.5 时才创建当前任务目录。

# Preflight

任何正式写入前确认：

- 当前 Task Sheet Step 为 2.5；
- 上游正式结果路径明确且可读；
- 2.3 输入按 nonstandard unit 解释；
- Workflow 1 chain assignment 已明确；
- final system composition 与 expected charge 等体系信息已给定；
- covalent attachment relationships 足以决定 automatic moleculetype merge；
- 多 unit overlap 已排除或已由用户处理；
- 需要用户决定的 `nrexcl`、`[ exclusions ]`、attachment-site atom type、parameter conflict 已在对应写入前解决；
- 当前 task-scoped 输出路径明确且不会覆盖其它任务正式结果。

Preflight 不通过时不得留下可误认成 final topology package 的结果。

# 用户确认

以下情况必须由当前 Task Execution Agent 向用户确认：

- 多个来源提供不同 `nrexcl`；
- `[ exclusions ]` 汇总去重后仍存在需要选择的情况；
- standard attachment-site old atom type 为 `NOT_APPLICABLE` 或 `UNRESOLVED`；
- parameter-definition same identity / different definition；
- 多个 nonstandard units 出现实质 overlap；
- 非 covalent topology-linked relation 的 final moleculetype organization 无法从已确认输入唯一决定；
- 任何不能机械确定的 topology ownership/conflict。

只要 blocking decision 未解决，2.5 保持 `未完成`；不新增 BLOCKED/WAITING 状态机。

# 完成与回写

2.5 完成后，由 Task Execution Agent：

- 在当前 Task Sheet 记录 final topology package 与 integration report；
- 将 official results 登记到 `project_result_index.md` 的 2.5 部分；
- 保留必要的用户关键决定与异常处理记录；
- 进入 2.6 时只交付 final topology package + integration report，不要求重读 2.5 全过程。

# Tool 边界

`.itp/.top` parsing、atom-index remapping、mechanical cleanup、parameter-definition normalization/dedup、map merge 等确定性动作适合后续实现为 deterministic Tool。

在共享 Tool 正式创建、测试并注册前，本 Skill 不为了方便而在业务执行时修改 `05_tools/`，也不要求构造 Legacy runtime input。

# 自检

- [ ] 以 nonstandard unit 而不是单个 nonstandard residue 解释 2.3 输出；
- [ ] 已消费 Workflow 1 chain assignment，未在 2.5 重新分 chain；
- [ ] covalently connected components 已归入同一 final moleculetype；
- [ ] final all-atom order / canonical final index / final map 在 topology integration 前已经冻结；
- [ ] 每个 final moleculetype `.itp` 直接由 topology integration 生成并使用 canonical final index；
- [ ] charge、bonded terms、pairs、exclusions 与 parameter definitions 均按 references 处理；
- [ ] 所有 blocking user decisions 已解决；
- [ ] final package 可确定性交给 2.6；
- [ ] 未重新引入 Legacy runtime orchestration。
