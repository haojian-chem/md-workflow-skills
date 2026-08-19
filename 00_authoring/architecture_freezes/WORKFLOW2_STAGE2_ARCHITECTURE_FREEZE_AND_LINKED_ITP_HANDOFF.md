# Workflow 2 Stage 2 架构冻结与 2.5 linked `.itp` integration 讨论交接

## 0. 文档定位

本文件记录 Workflow 2 Stage 2 已冻结架构，以及 `2.5 Topology integration and assembly` 的关键集成规则。

当前状态：

- Stage 2 需要阶段级 main Skill；其未来 runtime entry 固定为 `02_topology_preparation/SKILL.md`，阶段级职责边界：**冻结**；
- `2.1–2.6` 的步骤结构、主要职责、核心输入输出关系和关键边界：**冻结**；
- `2.1 Parameterization environment and assignment` 保持完整独立 Step，不部分或整体并入 Stage 2 main Skill：**冻结**；
- `2.5 linked .itp integration` 的主要 molecule-level / parameter-level 科学规则：**冻结到当前版本**；
- 核酸/DNA/RNA 的 2.3 截断细节：**尚未专项冻结**；
- 最终文件 basename / schema / 目录名：**仍可在实现层细化**；
- **Stage 2 尚未获批生成 active Skill；Stage 2 main Skill 与当前 2.1–2.6 scientific directories 均仍为 freeze-only / reserved package paths。**

2.5 更详细、可直接用于后续 Skill generation 的冻结材料位于：

```text
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_FREEZE.md
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md
```

这些文件保存此前未经授权物化的 2.5 guide/reference 细节，但它们仍是 architecture-freeze authoring input，不是 runtime Skill。

---

# 1. Stage 2 总体架构

Workflow 2 的目标是：从 Workflow 1 已完成结构识别、分类、选择、整理和重原子层面准备的结构出发，建立可用于后续体系构建的完整全原子 topology package，并在交给 Workflow 3 前完成 topology validation。

Stage 2 冻结为六个步骤：

1. `2.1 Parameterization environment and assignment`
2. `2.2 Standard residue topology generation`
3. `2.3 Topology-linked nonstandard parameterization`
4. `2.4 Independent nonstandard parameterization`
5. `2.5 Topology integration and assembly`
6. `2.6 Topology validation`

对象分类沿用 Workflow 1 / 1.2：

- `STANDARD_RESIDUE`
- `TOPOLOGY_LINKED_NONSTANDARD`
- `INDEPENDENT_NONSTANDARD`
- `SOLVENT_COMPONENT`
- `ION_COMPONENT`

`TOPOLOGY_LINKED_NONSTANDARD` 不等于“共价连接非标残基”。它表示该对象的 topology/parameterization 必须与另一个组件的 topology relation 联合处理，包括共价连接，也可包括被定义为 topology-forming 的配位关系。

## 1.1 Stage 2 main Skill

Stage 2 需要阶段级 main Skill。未来正式生成后的 runtime entry 固定为：

```text
02_topology_preparation/SKILL.md
```

该 main Skill 的独立职责是 **Stage 2 内部科研编排与跨 2.1–2.6 的共享接口语义**，而不是重新执行任何一个 2.x Step 的科研处理。

Stage 2 的总体执行关系为：

```text
Manager
→ 按已定义 catalog 建立初始 Task Sheet
→ Task Execution Agent 进入 Stage 2
→ Stage 2 main Skill
→ 2.1 产生当前体系的 parameterization environment / assignment result
→ Stage 2 main Skill依据该正式结果维护尚未执行的 Stage 2 计划
→ 2.2 / 2.3 / 2.4 按实际对象完成 topology acquisition / parameterization
→ Stage 2 main Skill确认当前 assignment 要求的上游结果已经齐备
→ 2.5 integration and assembly
→ 2.6 topology validation
```

Manager 仍只负责初始 Task Sheet planning，不读取 Stage 2 科研结果判断具体 scientific applicability。普通执行过程中不返回 Manager 调度；Stage 2 main Skill只拥有 Stage 2 内部、必须依据当前科研结果才能确定的计划调整与跨 Step 关系。

Stage 2 main Skill **不是独立编号 Step**，不在 Task Sheet 中创建 `2.0`、`Stage 2 planning` 或其它额外规划环节，也不创建 `stage2_plan.yaml`、route 对象或第二套 runtime state。Task Sheet 继续是 Stage 2 计划载体。

## 1.2 2.1 与 Stage 2 main Skill 的边界

`2.1 Parameterization environment and assignment` 保持完整独立科研 Step。

2.1 负责：

- 当前体系 parameterization environment 的建立；
- Stage 2 processing objects 的拆分 / 聚合；
- topology-linked nonstandard unit 的识别；
- independent nonstandard topology type 的识别；
- FF-direct solvent / ion 与需要进入 2.4 的 solvent / ion 的区分；
- 各实际对象的 topology acquisition / parameterization assignment；
- 2.1 正式结果及其 validation / reuse 语义。

Stage 2 main Skill不重新做这些科学判断，也不把 2.1 拆成“Stage-level environment + Step-level assignment”两套职责。

Stage 2 main Skill只消费 2.1 已确认的当前正式结果，并据此维护下游计划与 2.5 进入条件：

```text
2.1 决定当前体系需要哪些参数化工作
Stage 2 main Skill据此维护其余 Stage 2 Task Sheet
```

如果 2.1 的 parameterization environment 或 assignment 在后续发生会影响既有结果语义的实质变化，Stage 2 main Skill必须重新核验受影响的下游工作是否仍满足当前 assignment；不因为上游变化机械重做全部未受影响结果，也不得在 2.5 进入条件判断中继续使用已经与当前 assignment 不一致的旧结果。

## 1.3 Stage 2 计划展开

Manager 可以按照 planning index 把 2.1–2.6 作为初始 catalog 写入 Task Sheet，但这不表示所有 2.2–2.4 工作都已被判定为实际适用。

2.1 完成后，Stage 2 main Skill根据当前正式 assignment 维护尚未执行的 Stage 2 计划：

```text
存在 STANDARD_RESIDUE
→ 保留一个 2.2 工作项处理当前体系全部标准残基
→ 2.2 内部的 pdb2gmx processing-group 拆分仍属于 2.2 内部实现，不因此拆成多个 2.2 Task Sheet 项

每个 topology-linked nonstandard unit
→ 一个 2.3 工作项

每个需要独立参数化的 topology type
→ 一个 2.4 工作项

FF-direct solvent / ion
→ 不建立 2.4 参数化工作项
→ 作为 2.5 的直接输入
```

因此 2.3 和 2.4 可以在同一 Task Sheet 中按实际对象出现多次。初始占位的 2.3 / 2.4 条目应按 2.1 的实际结果替换、展开或删除，而不是为了保持 catalog 外观保留无对象的空步骤。

Stage 2 main Skill只根据 2.1 的正式 assignment 展开执行对象，不自行重新分类 residue、重建 topology-linked unit 或重新选择参数化方法。

## 1.4 2.5 输入就绪条件与汇合关系

Stage 2 的实际工作集合由 2.1 决定；2.2 / 2.3 / 2.4 按对象展开，随后在 2.5 统一汇合。

进入 2.5 前，Stage 2 main Skill必须对照**当前有效的 2.1 assignment**确认所有必要上游结果已经齐备：

- 若存在 `STANDARD_RESIDUE`，当前体系已有满足当前 assignment 的有效 2.2 结果；
- 每个 topology-linked nonstandard unit 都已有满足当前 assignment 的有效 2.3 结果；
- 每个需要独立参数化的 topology type 都已有满足当前 assignment 的有效 2.4 结果；
- 每个 FF-direct solvent / ion 都仍能从当前 parameterization environment 定位到 2.1 已确认的完整 topology definition；
- 不存在尚未解决、会导致当前体系 topology acquisition 不完整的 assignment 项。

这里的阶段级检查只判断**当前 assignment 要求的结果覆盖是否闭合**。它不重新执行 2.2 / 2.3 / 2.4 的科学 validation，也不替 2.5 检查实际 integration artifact 的内部一致性。

2.5 自己仍负责确认其实际输入文件 / definition 可以读取并用于 assembly，以及完成 integration / assembly 的具体 validation。Stage 2 main Skill不得通过重新推断整个体系组成来替代 2.1，也不得通过重复检查上游结果内部科学细节来替代各结果 owner。

## 1.5 2.6 与 Stage 2 completion

2.6 是 Stage 2 final validation owner。Stage 2 main Skill不建立第二套 final validation，也不另造阶段级结果包。

如果 2.6 识别到阻断性问题，2.6 只报告问题及其真正 owner；Stage 2 main Skill据此维护尚未完成或需要重新进入的 Stage 2 计划，使问题回到对应的 2.1–2.5 owner 处理。

若修正改变了 2.5 final package，则必须在必要的 2.5 assembly 更新后重新进入 2.6。只有当前任务所需的 Stage 2 工作已闭合、2.5 final package 为当前有效版本且正式 2.6 validation 通过，Stage 2 才完成并可交给 Workflow 3。

## 1.6 Stage 2 共享接口

跨多个 Stage 2 producer / consumer 且必须保持统一语义的接口，由 Stage 2 main Skill拥有统一的阶段级接口定义；具体生成算法仍由各 Step owner 拥有。

当前已冻结的统一 `*.map` 语义属于 Stage 2 共享接口。正式 Skill generation 时，其详细接口定义可以放在 Stage 2 main Skill 自己的 local reference 中，由 2.2 / 2.3 / 2.4 / 2.5 按需引用；不得在多个 Step Skill 中各维护一份可独立漂移的重复规范。

2.1 产生的 parameterization environment / assignment result仍由 2.1 拥有；Stage 2 main Skill只负责确保后续科研编排与 2.5 进入条件使用同一当前有效结果，不建立第二份阶段级 assignment record。

---

# 2. 2.1 Parameterization environment and assignment

## 2.1 目标

2.1 只做两件事：

1. 建立当前体系后续使用的 parameterization environment；
2. 把实际对象分配给 2.2–2.5 的具体 topology acquisition / parameterization 路线。

2.1 不重新执行 1.2 分类，也不承担 Manager 式计划判断。

## 2.2 Parameterization environment

一个体系允许混合使用多个 force-field / parameter definition source，因此环境应抽象为：

```text
set of force-field / parameter definition sources
```

而不是单一 force-field path。

多个来源并存不自动构成冲突。只有同名不同定义、同一参数对象存在不兼容定义或其它真实 coverage 冲突时，才需要处理。

## 2.3 对象 assignment

### STANDARD_RESIDUE

全部标准残基整体分配给 2.2：

```text
all STANDARD_RESIDUE
→ 2.2
```

这里的“整体”只表示 2.1 的 assignment 粒度，不代表 2.2 只能运行一次 `pdb2gmx`。2.2 内部可根据实际软件/科学要求拆分 processing group。

### TOPOLOGY_LINKED_NONSTANDARD

2.1 必须识别需要联合参数化的 **topology-linked nonstandard unit**。

一个 unit 可以包含一个或多个 nonstandard residues；只要这些 residues 在参数化上必须作为同一 linked chemical unit 联合处理，就属于同一个 2.3 processing unit。

```text
one topology-linked nonstandard unit
→ one 2.3 processing unit
```

不得把“一个 nonstandard residue = 一个 2.3 processing unit”作为固定规则。

### INDEPENDENT_NONSTANDARD

按 residue name/type 处理。同一 residue name 在 Stage 2 默认代表同一 topology type，只参数化一次。

若同名实例需要不同参数化，应先赋予不同 residue names，保证：

```text
one residue name → one topology definition
```

### ION_COMPONENT / SOLVENT_COMPONENT

若 parameterization environment 已提供完整 molecule topology definition，则不再经过 topology generation，2.5 直接使用。

若缺少完整定义，则按 independent nonstandard type 进入 2.4。

关键区分：

```text
STANDARD_RESIDUE
→ force field 提供 residue/template definition
→ 2.2 仍需为当前体系生成 molecule topology

FF-defined solvent / ion
→ force field 已有完整 topology include
→ 2.5 可直接使用
```

---

# 3. 2.2 Standard residue topology generation

2.2 为当前体系全部 `STANDARD_RESIDUE` 生成实际的全原子 structure + topology。

输入：Workflow 1 标准残基重原子结构 + 2.1 parameterization environment / assignment。

2.2 内部可按实际需要拆分 `pdb2gmx processing groups`，但不把 `one chain = one pdb2gmx run` 作为默认规则。

2.2 负责 `STANDARD_RESIDUE` 补氢。

主要输出：

```text
standard-only .gro
standard-only .top
standard molecule .itp file(s)
corresponding *.map
```

---

# 4. 统一 `*.map` 规则

`*.map` 是 Stage 2 共享接口；其统一接口定义由 Stage 2 main Skill拥有，2.2 / 2.3 / 2.4 负责按该定义生成各自产物，2.5 负责按同一接口消费，不在各 Step 内重新定义第二套 map 语义。

`*.map` 只回答“当前输出原子是谁、来自哪里”，不承担 connectivity、bond 描述、topology-link 删除逻辑或 linked-site chemical decision。

映射方向固定为：

```text
generated/output atom → source provenance
```

字段：

```yaml
output_atom_index:
output_atom_name:
output_residue_name:
output_residue_number:
origin: SOURCE | ADDED_H | CAP
source_atom_serial:
```

- `SOURCE`：`source_atom_serial` 必填；
- `ADDED_H`：`source_atom_serial` 为空；
- `CAP`：`source_atom_serial` 为空；
- 不加入 `DELETED_BY_LINK`；
- ADDED_H 的连接归属从 `.itp [ bonds ]` / `.mol2` 读取，不在 map 重复保存。

---

# 5. 2.3 Topology-linked nonstandard parameterization

## 5.1 处理单位

2.3 的处理单位是 **topology-linked nonstandard unit**，不是单个 residue。

一个 unit 可以由一个或多个 nonstandard residues 组成；unit 内不同 residues 仍保持各自 residue identity。

## 5.2 主要职责

2.3 负责：

- 确定 parameterization model 范围；
- 从 2.2 提取标准侧 all-atom fragment；
- 从 Workflow 1 提取 unit 内 nonstandard source atoms；
- 仅对 unit 内 nonstandard 部分补氢；
- 判断 topology link 导致的标准侧多余原子；
- 添加 parameterization cap；
- 完成 DFT / RESP(2) / Sobtop；
- 建立 mapping；
- 向 2.5 输出 linked-site modification 信息。

2.3 不直接修改 2.2 baseline topology/structure。

## 5.3 standard fragment 来源

2.3 parameterization model 中的 standard fragment 来自 2.2 all-atom structure，包含 2.2 新增 H，并保持其在 2.2 中的相对 atom order。

2.3 不重新给 standard fragment 补氢。

## 5.4 standard-side deletion

2.3 根据已确认 topology relation 判断标准侧哪些新增原子与 linked 状态不兼容，并在参数化模型中删除；2.2 baseline 保持不变。

```text
2.3 → 判断 standard-side modification
2.5 → 在最终 topology / structure 中实际应用
```

## 5.5 参数化模型截取

蛋白默认原则：完整保留直接相连 residue A，向 A-1/A+1 扩展，跨过肽键后尽量在合适 C-C 单键处截断，并以 H 形成 methyl-like cap。

核酸/DNA/RNA 的 phosphodiester boundary / O3' / O5' capping 仍需专项冻结。

## 5.6 atom order

完成 extraction + standard-side deletion + nonstandard hydrogenation + capping 后，参数化模型 atom order 冻结。

后续 `.mol2 / .map / OPT / FREQ / SP / .chg / Sobtop / .gro / .itp` 必须保持可确定的一致 atom-index 对应。

## 5.7 DFT / charge 路线

```text
prepared model
→ OPT
→ 基于 optimized structure 一起生成 FREQ + SP task files
→ FREQ / SP
→ Multiwfn
→ RESP / RESP2
→ .chg
→ Sobtop
```

具体 level of theory、basis、solvent model、RESP/RESP2 settings 不在架构层写死。

## 5.8 输出

每个 unit 至少：

```text
*.mol2
*.chg
*.itp
*.gro
*.map
linked-site modification information
```

`.top` 若实际生成且有复现价值可保留，但不是强制核心 handoff。

---

# 6. 2.4 Independent nonstandard parameterization

2.4 按 residue name / topology type 参数化；同一 type 只做一次参数化。

主路线：

```text
select representative instance
→ extract
→ hydrogenate
→ freeze atom order
→ mol2 + map
→ OPT
→ FREQ + SP
→ Multiwfn
→ RESP / RESP2
→ chg
→ Sobtop
→ itp / gro
```

2.4 不读取 2.2 standard fragment，不处理 topology link，不需要 CAP，不修改 standard residue。

固定输出层级：

```text
type-level:
  mol2 / chg / itp

system-instance-level:
  gro / map   # 当前体系该 type 的全部实例
```

---

# 7. Workflow 1 → Stage 2 的 chain assignment handoff

Stage 2 不自行重新给 topo-linked nonstandard unit 分 chain；它消费 Workflow 1 最终结构整理/映射阶段已经确定的 chain assignment。

规则：

```text
一个 topo-linked unit 的 standard-side linked residues 全部属于同一条 standard chain
→ unit 不单独设 chain，归入该 chain

一个 topo-linked unit 的 standard-side linked residues 跨多条 standard chains
→ unit 单独设 chain
```

这是结构 identity / ordering 规则，不等同于 GROMACS `moleculetype` 组织。

即使多个 chain 因共价 topology 在 2.5 中合并成一个 final moleculetype，原 chain identity 仍保留。

---

# 8. 2.5 Topology integration and assembly

## 8.1 目标

将 2.2 standard、2.3 topology-linked nonstandard units、2.4 independent nonstandard，以及 FF-direct solvent/ion definitions 整合为完整 final all-atom topology package。

## 8.2 final moleculetype 组织

自动组织以已确认 covalent connectivity 为准：

```text
unit 只共价连接一个现有 moleculetype
→ 并入该 final moleculetype

unit 同时共价连接多个现有 moleculetype
→ 所有相关 standard components + unit 合并成一个 final moleculetype
```

chain identity / residue identity 保留；改变的是 GROMACS `moleculetype` 组织。

非 covalent topology-linked relation 若无法从上游唯一确定 final moleculetype organization，则向用户确认。

## 8.3 coordinate ownership

- 2.2：贡献全部 STANDARD_RESIDUE coordinates，并应用 2.3 confirmed deletions；
- 2.3：只贡献 unit 自身最终存在的 SOURCE + ADDED_H atoms，不贡献 standard parameterization fragment / CAP；
- 2.4：贡献 all-instance structure/map；
- FF-direct solvent/ion：贡献当前体系实际实例坐标，topology definition 使用 2.1 指定来源。

## 8.4 final all-atom order 必须先于 topology integration

2.5 的顺序固定为：

```text
1. 固定 2.5 输入集合
2. 确定 final topology / moleculetype organization
3. 按 coordinate ownership 确定 final atom set，并应用 confirmed standard-side deletions
4. 建立 final all-atom order
5. 同时生成 canonical final atom index + final.map + local/source → final index mapping
6. 以这套 final index 为目标，对每个 final moleculetype 执行 topology integration，直接生成 final molecule .itp
7. 汇总 / 去重 / 冲突检查 global/type-level parameter definitions，生成 dedicated parameter-definition .itp
8. 组装 final_system.top（includes + [ system ] + [ molecules ]）
9. 按第 4–5 步已经冻结的顺序写 final_system.gro
10. 执行 2.5 assembly completeness gate，并交给 2.6
```

因此 final all-atom order / final.map 不是 topology integration 的结果，而是 topology integration 与 coordinate writing 的共同 canonical index 基础。

## 8.5 final all-atom ordering rules

Workflow 1 只提供 heavy-atom identity/order 骨架。

- STANDARD_RESIDUE 内部：继承 2.2 all-atom order，减去 2.3 deletion targets；其余相对顺序不变；
- topo-linked unit 内：只保留 unit 自身最终 SOURCE + ADDED_H atoms，排除 standard fragment / CAP，并保持 2.3 相对顺序；
- independent instances：继承 2.4 all-instance order；
- linked nonstandard block 不按 attachment site 紧邻插入 standard residue，而是在所属 standard residue block 之后按 Workflow 1/object order 组织；
- 只做 final moleculetype organization 所需的块级组合，不自由重排。

## 8.6 molecule-level topology integration

每个 final moleculetype 的 final `.itp` 是第 6 步 topology integration 的直接输出。

详细冻结规则见：

```text
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md
```

包括：

- `[ atoms ]` integration；
- standard-side deletion cleanup；
- attachment-site atom type applicability review；
- `S_mod + U` charge modification；
- `[ bonds ] / [ angles ] / [ dihedrals ]` migration；
- `[ pairs ]` special handling；
- `[ exclusions ]`；
- other molecule-level directives；
- multiple-unit overlap；
- final coordinate / map alignment。

## 8.7 global/type-level definitions

需要从 2.2–2.4 收集并统一处理：

```text
[ atomtypes ]
[ bondtypes ]
[ angletypes ]
[ dihedraltypes ]
[ pairtypes ]
[ nonbond_params ]
```

规则：extract → collect → internal dedup → 与实际 FF include tree 第二轮 dedup → conflict check → dedicated parameter-definition `.itp`。

`same identity + same definition` 去重；`same identity + different definition` 为 blocking conflict，不静默覆盖。

详细冻结规则见：

```text
00_authoring/architecture_freezes/WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md
```

## 8.8 2.5 official results

至少：

```text
final_system.top
final_system.gro
final_system.map
all final local molecule .itp files
one consolidated parameter-definition .itp
topology_integration_report.yaml
```

---

# 9. 2.6 Topology validation

2.6 不构建 topology，只验证 2.5 package 是否可可靠交给 Workflow 3。

至少覆盖：

- package/include 完整性；
- molecule topology 内部一致性；
- linked modifications 是否完整应用；
- standard-side charge update 是否落地；
- topology ↔ coordinate ↔ final.map 逐原子一致性；
- final.map provenance 完整性；
- charge/connectivity sanity；
- GROMACS preprocessing (`gmx grompp`)。

`grompp success != full 2.6 pass`。

2.6 不顺手修 topology；失败时回到对应上游修正。

---

# 10. Stage 2 冻结状态

## 已冻结

- Stage 2 设置阶段级 main Skill，未来 runtime entry 为 `02_topology_preparation/SKILL.md`；
- Stage 2 main Skill拥有 Stage 2 内部科研编排、由 2.1 正式结果驱动的下游计划维护、2.5 输入就绪条件、2.6 失败后的 Stage 2 计划调整，以及 Stage 2 共享接口定义；
- Stage 2 main Skill不是编号 Step，不建立额外规划 Step、`stage2_plan.yaml`、route 对象或第二套 runtime state；
- 2.1 保持完整独立科研 Step，parameterization environment / object assignment 不部分或整体移入 Stage 2 main Skill；
- 2.1–2.6 六步架构；
- 2.1 assignment 与 parameterization environment；
- 2.1 结果驱动 2.2 / 2.3 / 2.4 实际 Task Sheet 工作集合展开：全部 standard residue 对应一个 2.2 工作项；每个 topology-linked unit 对应一个 2.3 工作项；每个需要独立参数化的 topology type 对应一个 2.4 工作项；FF-direct solvent / ion 不创建 2.4 参数化工作项；
- 2.5 进入前必须对照当前有效 2.1 assignment 确认所有 topology acquisition / parameterization 所需结果已经齐备；
- 2.3 processing unit = topology-linked nonstandard unit，可包含一个或多个 nonstandard residues；
- 2.2 / 2.3 / 2.4 主要职责与输出层级；
- map 基本职责与字段，并作为 Stage 2 共享接口由未来 Stage 2 main Skill统一拥有接口定义；
- 2.3 判断 standard-side deletion、2.5 执行；
- Workflow 1 → Stage 2 的 topo-linked chain assignment handoff；
- 2.5 final moleculetype organization；
- 2.5 coordinate ownership；
- final all-atom order / canonical final index / final.map 必须先于 topology integration；
- 每个 final moleculetype `.itp` 由 topology integration 直接生成；
- 2.5 molecule-level linked integration 当前规则；
- 2.5 global parameter definition collection/dedup/conflict handling；
- 2.6 validation boundary；
- Stage 2 completion 由当前有效 2.5 final package + 正式 2.6 validation pass 闭合，Stage 2 main Skill不建立第二套 final validation 或重复结果包。

## 仍可继续细化但不重新开放 Stage 2 架构

- Stage 2 main Skill 正式生成时的 main/reference 文本组织与具体 reference basename；
- 2.1 正式结果 basename / schema 与实现细节；
- 核酸/DNA/RNA 的 2.3 截断/capping 规则；
- 文件 basename、schema、deterministic tool implementation；
- validator/testing fixture 与实现细节；
- 新科学证据明确要求的局部规则修订。

Stage 2 从此视为 **architecture frozen**。后续只有在用户明确批准对应 Stage main Skill / Step Skill / Tool generation 后，才把这些 freeze 转写为 active implementation；不因 freeze 足够详细而自动生成 runtime Skill。