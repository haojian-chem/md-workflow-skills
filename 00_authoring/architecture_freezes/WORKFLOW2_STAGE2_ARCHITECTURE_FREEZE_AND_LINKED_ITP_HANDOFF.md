# Workflow 2 Stage 2 架构冻结与 2.5 linked `.itp` integration 讨论交接

## 0. 文档定位

本文件记录 Workflow 2 Stage 2 已冻结架构，以及 `2.5 Topology integration and assembly` 的关键集成规则。

当前状态：

- Stage 2 需要阶段级 main Skill；其未来 runtime entry 固定为 `02_topology_preparation/SKILL.md`，阶段级职责边界：**冻结**；
- `2.1–2.6` 的步骤结构、主要职责、核心输入输出关系和关键边界：**冻结**；
- `2.1 Topology preparation setup` 保持完整独立 Step，不部分或整体并入 Stage 2 main Skill；当前 active entry 为 `02_topology_preparation/2.1_topology_preparation_setup/SKILL.md`；
- `2.3 Topology-linked nonstandard parameterization` 的建立参数化模型科学规则，包括一般范围规则、蛋白质截取/封端、核酸截取/封端、标准残基一侧原子变化、非标准残基补氢与 map 维护：**已专项冻结**；
- `2.3` 的量化计算主线由 `WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md` 拥有；几何优化固定原子规则已经专项冻结到当前版本；
- `2.3` 的 RESP / RESP2 电荷拟合科学规则：**已专项冻结**；
- `2.3` 的 Sobtop 参数化当前已敲定规则：**已专项冻结**；
- `2.3` 的当前科研处理环节、六个核心结果文件、正式结果记录及向 2.5 交付的信息：**已冻结到当前版本**；
- `2.5 linked .itp integration` 的主要 molecule-level / parameter-level 科学规则：**冻结到当前版本**；
- 尚未固定的其它文件 basename / schema / 目录名：**仍可在实现层细化**；
- **当前只有 2.1 已生成 active Skill；Stage 2 main Skill 与 2.2–2.6 仍为 freeze-only / reserved package paths。**

2.3 当前详细冻结材料位于：

```text
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md
WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md
WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.3_SOBTOP_PARAMETERIZATION_RULES_FREEZE.md
```

2.5 更详细、可直接用于后续 Skill generation 的冻结材料位于：

```text
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_FREEZE.md
WORKFLOW2_STAGE2_2.5_TOPOLOGY_INTEGRATION_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.5_PARAMETER_DEFINITION_DEDUPLICATION_FREEZE.md
```

这些文件都是 architecture-freeze authoring input，不是 runtime Skill。

---

# 1. Stage 2 总体架构

Workflow 2 的目标是：从 Workflow 1 已完成结构识别、分类、选择、整理和重原子层面准备的结构出发，建立可用于后续体系构建的完整全原子 topology package，并在交给 Workflow 3 前完成 topology validation。

Stage 2 冻结为六个步骤：

1. `2.1 Topology preparation setup`
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
→ 2.1 确定当前使用的力场及其它参数定义来源、判断已有 Stage 2 正式结果适用性，并直接把实际 2.2–2.5 工作项写入 Task Sheet
→ Stage 2 main Skill维护后续 Stage 2 工作项的完成状态与跨 Step 关系
→ 2.2 / 2.3 / 2.4 按实际对象完成 topology acquisition / parameterization
→ Stage 2 main Skill确认 2.1 已确定的必要上游工作已经齐备
→ 2.5 integration and assembly
→ 2.6 topology validation
```

Manager 仍只负责初始 Task Sheet planning，不读取 Stage 2 科研结果判断具体 scientific applicability。普通执行过程中不返回 Manager 调度；Stage 2 main Skill只拥有 Stage 2 内部、必须依据当前科研结果才能确定的计划调整与跨 Step 关系。

Stage 2 main Skill **不是独立编号 Step**，不在 Task Sheet 中创建 `2.0`、`Stage 2 planning` 或其它额外规划环节，也不创建 `stage2_plan.yaml`、route 对象或第二套 runtime state。Task Sheet 继续是 Stage 2 计划载体。

## 1.2 2.1 与 Stage 2 main Skill 的边界

`2.1 Topology preparation setup` 保持完整独立科研 Step。

2.1 负责：

- 确定当前体系实际使用的力场及其它参数定义来源，并记录实际路径；
- 多来源情况下检查当前 `STANDARD_RESIDUE` 是否在多个来源中重复定义，并明确实际采用的定义来源；
- 依据 1.2 分类与已确认拓扑关系，确定当前体系实际需要的 2.2–2.5 处理对象；
- 从 `project_result_index.md` 检索已有 2.2–2.5 正式结果，并按 2.1 current Skill 的规则判断其是否适用于当前体系；
- 直接更新当前 Task Sheet，使 2.2–2.5 工作项与当前体系实际处理对象一致。

2.1 的规划信息直接写入 Task Sheet，不生成独立的 Stage 2 assignment result 或第二份规划记录。

Stage 2 main Skill不重新做上述科学判断。2.1 完成后，Stage 2 main Skill维护这些工作项的完成状态、跨 Step 关系与后续 2.5 进入条件。

若后续实际使用的力场、参数定义来源或处理对象发生实质变化，受影响的 2.2–2.5 工作项及已有正式结果适用性必须重新核验；不因为局部变化机械重做全部未受影响结果。

## 1.3 Stage 2 计划展开

Manager 可以按照 planning index 把 2.1–2.6 作为初始 catalog 写入 Task Sheet，但这不表示所有 2.2–2.4 工作都已被判定为实际适用。

2.1 根据当前体系直接维护尚未执行的 2.2–2.5 工作项：

```text
存在 STANDARD_RESIDUE
→ 一个 2.2 工作项处理当前体系全部标准残基

每个实际需要共同参数化的 TOPOLOGY_LINKED_NONSTANDARD 残基组合
→ 一个 2.3 工作项

每个需要独立参数化的 residue name
→ 一个 2.4 工作项

已有完整 molecule topology definition 的 SOLVENT_COMPONENT / ION_COMPONENT
→ 不建立对应 2.4 工作项
→ 作为 2.5 的直接输入

当前体系
→ 保留一个 2.5 工作项
```

因此 2.3 和 2.4 可以在同一 Task Sheet 中按实际对象出现多次。初始占位但没有当前实际处理对象的 2.2–2.4 条目可由 2.1 按 Task Execution 通用规则调整；已有实际执行历史的条目不得为了整理计划而静默删除。

Stage 2 main Skill在 2.1 之后只维护当前已经确定的工作集合与完成状态，不重新分类 residue、不重新决定 2.3 组合，也不重新选择 2.1 已确认的力场/参数定义来源。

## 1.4 2.5 输入就绪条件与汇合关系

Stage 2 的实际工作集合由 2.1 在 Task Sheet 中确定；2.2 / 2.3 / 2.4 按对象展开，随后在 2.5 统一汇合。

进入 2.5 前，Stage 2 main Skill必须对照当前 Task Sheet 中由 2.1 确定的处理对象和直接输入，确认所有必要上游结果已经齐备：

- 若存在 `STANDARD_RESIDUE`，当前体系已有满足当前对象与力场要求的有效 2.2 结果；
- 每个 2.3 工作项都已有与其当前处理对象对应的有效 2.3 结果；
- 每个 2.4 工作项都已有与其当前 residue name / component 对应的有效 2.4 结果；
- 直接进入 2.5 的 `SOLVENT_COMPONENT` / `ION_COMPONENT` 仍能从 2.1 已记录的实际来源定位到完整 molecule topology definition；
- 不存在尚未解决、会导致当前体系 topology acquisition 不完整的 2.2–2.5 工作项。

这里的阶段级检查只判断当前 Task Sheet 要求的结果覆盖是否闭合。它不重新执行 2.2 / 2.3 / 2.4 的科学 validation，也不替 2.5 检查实际 integration artifact 的内部一致性。

2.5 自己仍负责确认其实际输入文件 / definition 可以读取并用于 assembly，以及完成 integration / assembly 的具体 validation。Stage 2 main Skill不得通过重新推断整个体系组成来替代 2.1，也不得通过重复检查上游结果内部科学细节来替代各结果 owner。

## 1.5 2.6 与 Stage 2 completion

2.6 是 Stage 2 final validation owner。Stage 2 main Skill不建立第二套 final validation，也不另造阶段级结果包。

如果 2.6 识别到阻断性问题，2.6 只报告问题及其真正 owner；Stage 2 main Skill据此维护尚未完成或需要重新进入的 Stage 2 计划，使问题回到对应的 2.1–2.5 owner 处理。

若修正改变了 2.5 final package，则必须在必要的 2.5 assembly 更新后重新进入 2.6。只有当前任务所需的 Stage 2 工作已闭合、2.5 final package 为当前有效版本且正式 2.6 validation 通过，Stage 2 才完成并可交给 Workflow 3。

## 1.6 Stage 2 共享接口

跨多个 Stage 2 producer / consumer 且必须保持统一语义的接口，由 Stage 2 main Skill拥有统一的阶段级接口定义；具体生成算法仍由各 Step owner 拥有。

当前已冻结的统一 `*.map` 语义属于 Stage 2 共享接口。正式 Skill generation 时，其详细接口定义可以放在 Stage 2 main Skill自己的 local reference 中，由 2.2 / 2.3 / 2.4 / 2.5 按需引用；不得在多个 Step Skill 中各维护一份可独立漂移的重复规范。

2.1 的力场/参数定义来源、已有正式结果引用以及 2.2–2.5 处理对象直接保存在当前 Task Sheet 中。Stage 2 main Skill只消费这一当前计划状态，不建立第二份阶段级 assignment record。

---

# 2. 2.1 Topology preparation setup

2.1 的 current runtime owner 为：

```text
02_topology_preparation/2.1_topology_preparation_setup/SKILL.md
```

本 freeze 只保留 2.1 的稳定架构边界：

1. 2.1 是独立科研 Step；
2. 2.1 确定当前体系实际使用的力场及其它参数定义来源；
3. 多来源时检查同一 `STANDARD_RESIDUE` 是否重复定义，并明确实际采用的定义来源；
4. 2.1 判断已有 2.2–2.5 正式结果对当前体系的适用性；
5. 2.1 根据当前对象把实际工作落实到 2.2–2.5，并直接更新 Task Sheet；
6. 2.1 本身不生成独立正式结果，不向 `project_result_index.md` 登记新的结果项。

具体处理对象划分、已有结果适用性判据和 Task Sheet 写入内容由 current `SKILL.md` 拥有，不在 freeze 中维护第二套可变规范。

---

# 3. 2.2 Standard residue topology generation

2.2 为当前体系全部 `STANDARD_RESIDUE` 生成实际的全原子 structure + topology。

输入：Workflow 1 标准残基重原子结构 + 当前 Task Sheet 中 2.1 已确定的力场/参数定义来源与 2.2 处理对象。

2.2 内部可按实际需要拆分 `pdb2gmx processing groups`，但不把 `one chain = one pdb2gmx run` 作为默认规则。

2.2 负责 `STANDARD_RESIDUE` 补氢。

主要输出：

```text
standard-only .gro
standard-only .top
standard molecule .itp file(s)
corresponding *.map
```

## 3.1 2.2 map 维护

2.2 的 `*.map` 以 Workflow 1 的 `stage1_final_map.yaml` 为直接身份与 provenance 基线，不重新从 `stage1_final.pdb` 的 chain、resid、residue name、atom name 或 atom order 推断身份。

对 2.2 输出中来自 Stage 1 最终结构的标准残基原子：

- 从 `stage1_final_map.yaml` 取得对应 record；
- 保留该 record 的 `original_atom_serial`、`component_id + residue_id` 和全部既有 `operations`；
- 只把当前 locator 更新为 2.2 standard-only 输出中的 `output_atom_index`。

2.2 新增的 H 在 Stage 1 map 中没有 atom record，因此建立新 record：

```text
original_atom_serial = null
component_id + residue_id = 该 H 所属标准残基的 1.2 正式身份
operations = [2.2ADD]
```

2.2 因只输出 `STANDARD_RESIDUE` 而未进入 standard-only 结构的其它 Stage 1 原子不写入 2.2 map；这属于当前输出 atom set 的限定，不建立删除记录。

---

# 4. 统一 `*.map` 规则

`*.map` 是 Stage 2 共享接口；其统一接口定义由 Stage 2 main Skill拥有。Stage 2 不在 2.2–2.4 重新初始化一套与 Workflow 1 无关的 provenance；凡能够对应到 `stage1_final_map.yaml` 的原子，都继续携带 Stage 1 已经建立的 identity 与 atom-level history。

Stage 2 map 的稳定逐原子核心字段为：

```yaml
output_atom_index:
original_atom_serial:
component_id:
residue_id:
operations:
```

字段语义：

- `output_atom_index`：该 record 对应原子在当前 map 所描述输出 atom order 中的索引；当前结构格式不要求为 PDB，因此不继续使用 `current_atom_serial` 作为 Stage 2 当前 locator；
- `original_atom_serial`：继续沿用 Stage 1 map 的语义，指向 Stage 1 map chain 的 `original_structure` 中对应 atom；原始结构中不存在对应 atom 时为 `null`；
- `component_id + residue_id`：继续使用 1.2 正式稳定 residue identity；对属于真实体系 residue 的原子必须成对存在；
- `operations`：保留 Stage 1 已有 operation history，并在 Stage 2 实际新增 atom 时追加/建立相应 Stage 2 operation code。

Stage 2 map 必须能够定位其直接使用的 `stage1_final_map.yaml` 与当前 map 所描述的 structure / atom-order artifact。具体文件级 basename 与最终 schema 仍留到 Stage 2 main Skill正式生成时统一物化；2.3 额外使用 2.2 map 作为 standard-side H 的 supporting mapping 时，由 2.3 正式结果同时定位该 supporting map。

当前为 2.2 / 2.3 冻结的 Stage 2 operation code：

```text
2.2ADD
2.3ADD
2.3CAP
```

- `2.2ADD`：2.2 新增、Stage 1 最终结构中不存在对应 atom 的 H；
- `2.3ADD`：2.3 为 `TOPOLOGY_LINKED_NONSTANDARD` residue 新增、Stage 1 最终结构中不存在对应 atom 的 H；
- `2.3CAP`：2.3 仅为 parameterization model 截断/封端而新增的临时 atom。

`2.3CAP` record 使用：

```text
original_atom_serial = null
component_id = null
residue_id = null
operations = [2.3CAP]
```

因为 CAP 不对应体系中的真实 residue atom。

Stage 2 map 不再把 provenance 压缩成 `origin: SOURCE | ADDED_H | CAP`，也不再使用单独的 `source_atom_serial` 替代 Stage 1 已维护的 `original_atom_serial + operations`。`output_atom_name / output_residue_name / output_residue_number` 由 `output_atom_index` 在当前 mapped structure 中读取，不在 map 中重复保存。

删除或未进入当前输出 atom set 的 atom 不在当前 map 中保留 tombstone record。Connectivity、bond 描述、topology-link standard-side deletion 判断仍由其正式 owner / artifact 表达，不重复塞入 map。

本次只冻结 2.2 / 2.3 的具体 map producer behavior；2.4 后续生成正式 Skill 时必须沿用上述共享核心字段与 Stage 1 identity/provenance continuity，再单独确认其所需 Stage 2 operation code 与具体维护方式。

---

# 5. 2.3 Topology-linked nonstandard parameterization

2.3 的当前详细 authority 为：

```text
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md
WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md
WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md
WORKFLOW2_STAGE2_2.3_SOBTOP_PARAMETERIZATION_RULES_FREEZE.md
```

## 5.1 处理单位

2.3 的处理单位是 **topology-linked nonstandard unit**，不是单个 residue。

一个 unit 可以由一个或多个 nonstandard residues 组成；unit 内不同 residues 仍保持各自 residue identity。

## 5.2 主要职责

2.3 负责：

- 建立当前处理对象的参数化模型；
- 从 2.2 提取参数化模型所需的标准残基全原子片段；
- 从 Workflow 1 提取当前处理对象中的 nonstandard source atoms；
- 对当前处理对象中的 nonstandard 部分补氢；
- 确定 topology link 导致的标准残基一侧原子变化；
- 按参数化模型边界进行封端；
- 完成量化计算；
- 完成电荷拟合并生成 `parameterization.chg`；
- 完成 Sobtop 参数化并生成 `parameterized_topology.itp`；
- 建立并维护 `parameterization_model.map`；
- 通过 `topology_linked_parameterization_result.yaml` 向 2.5 交付六个核心结果、标准残基一侧需要删除的原子和残基级电荷修改范围。

2.3 不直接修改 2.2 baseline topology/structure。

## 5.3 standard fragment 来源

2.3 parameterization model 中的 standard fragment 来自 2.2 all-atom structure，包含 2.2 新增 H，并保持其在 2.2 中的相对 atom order。

2.3 不重新给 standard fragment 补氢。

2.3 的 map baseline 仍是 `stage1_final_map.yaml`；2.2 map 只作为 standard fragment 中 Stage 1 不存在的新增 H 及其 `component_id + residue_id` / `2.2ADD` history 的 supporting mapping，不把 2.3 map 改成 2.2 map 的继承链。

## 5.4 标准残基一侧的原子变化

2.3 根据已确认 topology relation 判断标准残基一侧哪些原子因 linked 状态形成而不应继续保留，并在参数化模型中删除；2.2 baseline 保持不变。

对应 2.2 标准残基全原子结构中的原子及导致该删除的 `relation_id` 记录到 `topology_linked_parameterization_result.yaml.standard_atom_deletions`，由 2.5 在最终 structure / topology integration 时实际应用。

## 5.5 建立参数化模型

参数化模型的范围、蛋白质与核酸的截取/封端、标准残基一侧原子变化、非标准残基补氢、atom map 和原子顺序规则统一读取：

```text
WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md
```

当前已经专项冻结：

- 一般参数化模型范围规则；
- 蛋白质体系的截取与封端规则；
- 核酸体系的 5′ / 3′ 外扩、O5′ / O3′ 封端及互补配对核苷酸处理规则；
- 标准残基一侧原子变化；
- 非标准残基补氢；
- `parameterization_model.map` 维护；
- 建立参数化模型时生成 `parameterization_model.mol2`、`parameterized_structure.gro`、`parameterization_model.map`，三者采用同一套已确定的 atom order。

其它适用体系的具体截取与封端规则继续在该专项 freeze 的一般规则下按需讨论和冻结。

## 5.6 map 维护

2.3 parameterization model 的 map 从 `stage1_final_map.yaml` 的稳定身份与 history 出发，并按实际进入 parameterization model 的 atom set 构造：

1. unit 内 nonstandard source heavy atoms，以及 standard fragment 中能够对应到 Stage 1 最终结构的 atoms：保留其 `stage1_final_map.yaml` record 的 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`，只更新 `output_atom_index`；
2. standard fragment 中由 2.2 新增、Stage 1 最终结构中不存在的 H：从 2.2 map 取得对应 record，保留 `original_atom_serial: null`、`component_id + residue_id` 和包含 `2.2ADD` 的 history，再更新为 2.3 parameterization-model `output_atom_index`；
3. 2.3 为 unit 内 nonstandard residue 新增的 H：新建 record，`original_atom_serial: null`，写入该 residue 的 `component_id + residue_id`，`operations = [2.3ADD]`；
4. parameterization cap atom：新建 `2.3CAP` record，不赋予 `component_id + residue_id`；
5. 因 parameterization-model 截取而未纳入的 atoms，以及标准残基一侧因 topology link 而在当前参数化模型中去除的 atoms，不进入当前 2.3 map；需要在 2.5 实际删除的标准残基原子由 `topology_linked_parameterization_result.yaml.standard_atom_deletions` 记录。

因此 2.3 map 不是 2.2 map 的整体 copy-and-update；它以 Stage 1 final map 为主 baseline，只对参数化模型中实际使用的 2.2-added standard H 读取并保留对应 2.2 map record/history。

## 5.7 atom order

完成参数化模型范围确定、标准残基一侧原子处理、nonstandard hydrogenation 和 capping 后，确定参数化模型的 atom set 与 atom order，并生成：

```text
parameterization_model.mol2
parameterized_structure.gro
parameterization_model.map
```

三者采用同一套 atom order。后续量化计算、电荷拟合生成的 `parameterization.chg` 以及 Sobtop 生成的 `parameterized_topology.itp` 必须沿用可确定的原子对应关系。

## 5.8 科研处理环节

2.3 当前科研处理环节为：

```text
建立参数化模型
→ 量化计算
→ 电荷拟合并生成 parameterization.chg
→ Sobtop 参数化并生成 parameterized_topology.itp
```

建立参数化模型和电荷拟合的详细科学规则已经分别专项保存；量化计算主线由 `WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md` 拥有，其中几何优化固定原子规则单独保存于 `WORKFLOW2_STAGE2_2.3_GEOMETRY_OPTIMIZATION_FIXED_ATOMS_FREEZE.md`。Sobtop 参数化当前已经敲定的规则保存于 `WORKFLOW2_STAGE2_2.3_SOBTOP_PARAMETERIZATION_RULES_FREEZE.md`，其余尚未敲定的详细规则继续在 2.3 设计中确定，不在 Stage 2 总架构中维护第二套规范。

## 5.9 正式结果

每个 2.3 工作项的六个核心结果固定为：

```text
parameterization_model.mol2
parameterization_model.map
parameterization.chg
charge_fitting_result.yaml
parameterized_structure.gro
parameterized_topology.itp
```

并生成：

```text
topology_linked_parameterization_result.yaml
```

作为本环节正式结果记录。该 YAML 统一登记六个核心结果的完整路径，并记录标准残基一侧需要删除的原子与残基级电荷修改范围。项目结果索引只登记 `topology_linked_parameterization_result.yaml`，不分别登记六个核心结果文件。

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

将 2.2 standard、2.3 topology-linked nonstandard units、2.4 independent nonstandard，以及 force-field/parameter-source direct solvent/ion definitions 整合为完整 final all-atom topology package。

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

- 2.2：贡献全部 `STANDARD_RESIDUE` coordinates，并应用 2.3 正式结果记录中的标准残基一侧原子删除；
- 2.3：只贡献 unit 自身最终存在的真实原子，包括原有原子和 2.3 为 unit 内非标准残基新增的 H；不贡献参数化模型中的 standard fragment / CAP；
- 2.4：贡献 all-instance structure/map；
- 直接进入 2.5 的 solvent/ion：贡献当前体系实际实例坐标，topology definition 使用当前 Task Sheet 中 2.1 已记录的实际来源。

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

- `STANDARD_RESIDUE` 内部：继承 2.2 all-atom order，减去 2.3 deletion targets；其余相对顺序不变；
- topo-linked unit 内：只保留 unit 自身最终存在的真实原子，排除 standard fragment / CAP，并保持 2.3 相对顺序；
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
- 按 2.3 正式结果记录中的 `charge_modification_scope` 应用 2.3 已完成的电荷拟合结果；
- `[ bonds ] / [ angles ] / [ dihedrals ]` migration；
- `[ pairs ]` special handling；
- `[ exclusions ]`；
- other molecule-level directives；
- multiple-unit overlap；
- final coordinate / map alignment。

2.5 不拥有 RESP / RESP2 的拟合规则；这些规则由 `WORKFLOW2_STAGE2_2.3_CHARGE_FITTING_RULES_FREEZE.md` 拥有。

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
- Stage 2 main Skill拥有 Stage 2 内部科研编排、2.1 完成后的下游工作状态维护、2.5 输入就绪条件、2.6 失败后的 Stage 2 计划调整，以及 Stage 2 共享接口定义；
- Stage 2 main Skill不是编号 Step，不建立额外规划 Step、`stage2_plan.yaml`、route 对象或第二套 runtime state；
- `2.1 Topology preparation setup` 保持完整独立科研 Step，直接确定力场/参数定义来源、已有 2.2–2.5 正式结果适用性和当前 2.2–2.5 处理对象，并更新 Task Sheet；
- 2.1 本身不生成独立正式结果，不向 `project_result_index.md` 登记新的结果项；
- 2.1–2.6 六步架构；
- 2.1 更新后的 Task Sheet 形成 2.2 / 2.3 / 2.4 实际工作集合：全部 standard residue 对应一个 2.2 工作项；每个实际需要共同参数化的非标准残基组合对应一个 2.3 工作项；每个需要独立参数化的 residue name 对应一个 2.4 工作项；已有完整 topology definition 的 solvent / ion 不创建对应 2.4 工作项；
- 2.5 进入前必须对照当前 Task Sheet 中由 2.1 确定的处理对象和直接输入，确认所有 topology acquisition / parameterization 所需结果已经齐备；
- 2.3 processing unit = topology-linked nonstandard unit，可包含一个或多个 nonstandard residues；
- 2.3 的科研处理环节为“建立参数化模型 → 量化计算 → 电荷拟合并生成 `parameterization.chg` → Sobtop 参数化并生成 `parameterized_topology.itp`”；
- 2.3 建立参数化模型的一般规则、蛋白质与核酸截取/封端、标准残基一侧原子变化、非标准残基补氢和 map 维护已经专项冻结；
- 2.3 量化计算的电子状态、OPT、FREQ 以及 RESP / RESP2 所需 SP 计算主线由 2.3 主 freeze 拥有；几何优化固定原子规则已经专项冻结到当前版本；
- 2.3 RESP / RESP2 的 `Q_expected`、unconstrained / constrained two-stage 拟合、RESP2 混合与检查规则已经专项冻结；
- 2.3 Sobtop 参数化中 FREQ 虚频及振动模式检查、OPT 结构生成拟合用 mol2、ORCA / Gaussian 频率结果文件、金属离子 LJ 参数预存组织及 Sobtop 输出名称修正规则已经专项冻结；
- 2.3 建立参数化模型时生成 `parameterization_model.mol2`、`parameterized_structure.gro`、`parameterization_model.map`，三者采用同一套已确定 atom order；
- 2.3 六个核心结果 basename 以及 `topology_linked_parameterization_result.yaml` 正式结果记录已经固定；项目结果索引只登记该正式结果记录；
- 2.2 / 2.3 / 2.4 主要职责与输出层级；
- map 共享核心字段沿用 Workflow 1 的稳定 residue identity、`original_atom_serial` 与 operation history；2.2 / 2.3 的 producer 维护规则已冻结；
- 2.3 判断标准残基一侧需要删除的原子并记录，2.5 实际应用；
- Workflow 1 → Stage 2 的 topo-linked chain assignment handoff；
- 2.5 final moleculetype organization；
- 2.5 coordinate ownership；
- final all-atom order / canonical final index / final.map 必须先于 topology integration；
- 每个 final moleculetype `.itp` 由 topology integration 直接生成；
- 2.5 molecule-level linked integration 当前规则；
- 2.5 global parameter definition collection/dedup/conflict handling；
- 2.6 validation boundary；
- Stage 2 completion 由当前有效 2.5 final package + 正式 2.6 validation pass 闭合，Stage 2 main Skill不建立第二套 final validation 或重复结果包。

## 当前实现状态

- 2.1：active Skill 已生成，current entry 为 `02_topology_preparation/2.1_topology_preparation_setup/SKILL.md`；
- Stage 2 main Skill：freeze-only；
- 2.2–2.6：freeze-only。

## 仍可继续细化但不重新开放 Stage 2 架构

- Stage 2 main Skill 正式生成时的 main/reference 文本组织与具体 reference basename；
- 2.3 Sobtop 参数化其余尚未敲定的详细规则；
- 其它适用体系的 2.3 参数化模型截取/capping 专项规则；
- 其余尚未固定的文件 basename、schema、deterministic tool implementation；
- validator/testing fixture 与实现细节；
- 新科学证据明确要求的局部规则修订。

Stage 2 从此视为 **architecture frozen**。2.1 的 current runtime 细节由 active `SKILL.md` 拥有；其余 Stage main / Step 只有在用户明确批准对应 Skill / Tool generation 后，才把这些 freeze 转写为 active implementation。