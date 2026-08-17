---
name: structure_preparation_workflow
description: 定义 Lightweight Runtime v2 下结构准备阶段的科学边界、子环节关系，以及 1.1–1.9 到实际 Operation/Validator Skill 的映射。该 Skill 不维护 route、Workstream、runtime decision 或事务闭环，也不替代具体子环节 Skill 的科学执行规则。
---

# 目标

将结构对象从来源识别推进到经过最终验证、可供后续 topology preparation 使用的结构结果。

本 Workflow 在 Lightweight Runtime v2 中只承担两类职责：

1. 说明结构准备阶段内各子环节之间的科学关系；
2. 将任务单中的 `1.1`–`1.9` 映射到当前环节真正需要加载的 Operation / Validator Skill。

Manager 的初始任务规划使用：

`00_manager/md_workflow_manager/references/workflow_plan_index.yaml`

不需要读取本 Workflow 来生成初始 Task Sheet。

# Runtime 使用方式

Task Execution Agent 从 `Txxxx.md` 确定当前要处理的子环节和对象。

当需要确认当前子环节对应的实际 Skill 或阶段内关系时，可读取本 Workflow，然后只加载当前子环节需要的 Skill。

正常运行不要求每完成一个子环节都重新经过 Workflow decision 或返回 Manager。

本 Workflow 不：

- 创建或修改任务单；
- 查询或修改 `project_result_index.md`；
- 执行复用等价性判断；
- 执行 Operation / Validator；
- 创建子 Agent；
- 维护 Workstream、route、event、artifact state 或 transaction；
- 返回 `workflow_route_fragment` 或 `workflow_decision`；
- 根据目录存在与否推断子环节完成；
- 为 Manager 判断某个子环节是否适用于当前体系。

# 阶段目录与任务隔离

结构准备的稳定基础目录为：

```text
01_structure_preparation/
├── 01_source_recognition/
├── 02_component_and_residue_classification/
├── 03_chain_and_residue_selection/
├── 04_altloc_occupancy_resolution/
├── 05_completeness_check/
├── 06_missing_region_completion/
├── 07_protein_protonation_assignment/
├── 08_reorder_and_mapping/
└── 09_validation/
```

这些目录可以在项目初始化时建立到子环节基础目录这一层。

不同任务的实际执行结果必须隔离在任务专属子目录：

```text
<base_work_directory>/<task_id>/
```

例如：

```text
01_structure_preparation/02_component_and_residue_classification/T001/
01_structure_preparation/02_component_and_residue_classification/T005/
```

Manager 在 Task Sheet 中记录任务专属工作目录路径，但不创建 `Txxxx/`。

`Txxxx/` 由 Task Execution Agent 在确认当前环节不能直接复用、确实需要执行时创建。若当前环节直接复用已有正式结果，则不要求创建空的本任务目录。

目录存在不是完成证据。

# 子环节到 Skill 的映射

## 1.1 Source recognition

基础工作目录：

`01_structure_preparation/01_source_recognition`

任务执行目录：

`01_structure_preparation/01_source_recognition/<task_id>`

当前执行 Skill：

`02_operations/source_recognition/SKILL.md`

逻辑职责：`OPERATION`

---

## 1.2 Component and residue classification

基础工作目录：

`01_structure_preparation/02_component_and_residue_classification`

任务执行目录：

`01_structure_preparation/02_component_and_residue_classification/<task_id>`

当前执行 Skill：

`02_validators/component_and_residue_classification_validator/SKILL.md`

逻辑职责：`VALIDATOR`

---

## 1.3 Chain and residue selection

基础工作目录：

`01_structure_preparation/03_chain_and_residue_selection`

任务执行目录：

`01_structure_preparation/03_chain_and_residue_selection/<task_id>`

当前执行 Skill：

- `02_operations/chain_and_residue_selection/SKILL.md`
- `02_validators/chain_and_residue_selection_validator/SKILL.md`

逻辑职责：`OPERATION + VALIDATOR`

---

## 1.4 Altloc occupancy resolution

基础工作目录：

`01_structure_preparation/04_altloc_occupancy_resolution`

任务执行目录：

`01_structure_preparation/04_altloc_occupancy_resolution/<task_id>`

当前执行 Skill：

- `02_operations/altloc_occupancy_resolution/SKILL.md`
- `02_validators/altloc_occupancy_validator/SKILL.md`

逻辑职责：`OPERATION + VALIDATOR`

---

## 1.5 Completeness check

基础工作目录：

`01_structure_preparation/05_completeness_check`

任务执行目录：

`01_structure_preparation/05_completeness_check/<task_id>`

当前执行 Skill：

`02_validators/structure_completeness_validator/SKILL.md`

逻辑职责：`VALIDATOR`

---

## 1.6 Missing region completion

基础工作目录：

`01_structure_preparation/06_missing_region_completion`

任务执行目录：

`01_structure_preparation/06_missing_region_completion/<task_id>`

当前执行 Skill：

- `02_operations/missing_region_completion/SKILL.md`
- `02_validators/missing_region_completion_validator/SKILL.md`

逻辑职责：`OPERATION + VALIDATOR`

---

## 1.7 Protein protonation assignment

基础工作目录：

`01_structure_preparation/07_protein_protonation_assignment`

任务执行目录：

`01_structure_preparation/07_protein_protonation_assignment/<task_id>`

当前执行 Skill：

- `02_operations/protein_protonation_assignment/SKILL.md`
- `02_validators/protein_protonation_validator/SKILL.md`

逻辑职责：`OPERATION + VALIDATOR`

---

## 1.8 Reorder and mapping

基础工作目录：

`01_structure_preparation/08_reorder_and_mapping`

任务执行目录：

`01_structure_preparation/08_reorder_and_mapping/<task_id>`

当前执行 Skill：

- `02_operations/structure_reorder_and_mapping/SKILL.md`
- `02_validators/structure_mapping_validator/SKILL.md`

逻辑职责：`OPERATION + VALIDATOR`

---

## 1.9 Validation

基础工作目录：

`01_structure_preparation/09_validation`

任务执行目录：

`01_structure_preparation/09_validation/<task_id>`

当前执行 Skill：

`02_validators/structure_preparation_validator/SKILL.md`

逻辑职责：`VALIDATOR`

# 阶段内科学关系

## 1.1 → 1.2

1.1 确定本任务后续处理使用的结构来源。1.2 对该结构进行链、组分、残基和关系分类。

1.2 不应通过重新做 source recognition 来恢复 1.1 的过程；需要来源信息时消费 1.1 的正式结果。

## 1.2 → 1.3

1.2 的正式分类结果是 1.3 理解 chain / component / residue 层级信息的上游依据。

1.3 不重新定义 1.2 已建立的分类标识和关系语义。

## 1.3 → 1.4

1.3 确定后续实际保留和处理的 target，并生成对应 PDB。1.4 直接读取这些 target PDB，对当前保留结构中的多 conformer / altloc 部分选择一个构象、删除其余构象原子并更新 atom serial。

若当前 target 不存在需要处理的多 conformer，Task Execution Agent 可按 1.4 Skill 的规则删除尚未执行的 1.4。

## 1.4 → 1.5

1.5 使用 1.4 后的当前 PDB，并结合前序已经完成的 residue / atom 核对信息，生成当前保留结构的 repair report。

报告范围包括：

- missing residues；
- missing heavy atoms；
- confirmed extra atoms；
- confirmed atom-name mismatches。

1.5 不重新执行前序 force-field / residue-definition 核对，也不修改结构。已确认属于正常 Stage 2 / `pdb2gmx` termini processing 的表示差异不作为 1.6 repair item。

## 1.5 → 1.6

1.6 严格按 1.5 repair report 执行：补 missing residues、补 missing heavy atoms、删除 confirmed extra atoms、校正已确认 atom-name mismatch。

缺失重原子可使用 AF3 / CCD 完整残基模板对齐后补全；缺失残基使用 AF3 完整结构作为参考，通过缺失区两侧逐步扩展的局部双侧 anchor 进行叠合后补全。两侧无法得到合理一致叠合时不得强行插入。

1.6 不重新判断 repair item，不执行 force-field-specific terminal conversion，也不生成最终 H。

如果 1.5 没有需要 1.6 处理的 repair item，可删除尚未执行的 1.6。

## 1.6 → 1.7

若 1.6 实际修改结构，1.7 必须消费 1.6 的 completed structure，而不是继续处理旧对象。

1.7 对蛋白质执行 PROPKA，并结合 PROPKA 结果与当前局部化学环境判断需要区分的 protonation state；随后把对应 residue name 改为目标 force field 的状态名称。1.7 不添加最终 H。

## 1.7 → 1.8

1.8 消费质子化状态已落实的重原子结构，确定最终 Stage 1 chain assignment、整理 residue / atom order 并生成 heavy-atom mapping。

对于 topology-linked nonstandard unit：

```text
all standard-side linked residues belong to one standard chain
→ assign the nonstandard unit to that chain

standard-side linked residues span multiple standard chains
→ give the nonstandard unit an independent chain identity
```

同一 chain 内 standard polymer residue block 保持 polymer 顺序；归入该 chain 的 topology-linked nonstandard units 放在 standard residue block 之后，并保持上游稳定 object order。

1.8 不再改变 heavy-atom set，也不生成 Stage 2 的 force-field-specific all-atom order。

## 1.8 → 1.9

1.9 对 `stage1_final.pdb + stage1_final.map` 执行阶段级只读验证，并再做一次最终 force-field compatibility check。

最终检查至少确认：

- Stage 1 上游 blocking 问题均已闭合；
- final PDB 与 map 一一对应；
- standard residue / protonation-state residue naming 可被目标 force field 识别；
- 1.6–1.8 修改后没有产生新的 blocking heavy-atom / atom-name incompatibility。

已确认属于 `pdb2gmx` 正常 termini processing 的 terminal representation 差异只记录为 Stage 2 handoff item，不作为 Stage 1 FAIL。1.9 不自行 repair；失败时返回真正负责的上游步骤处理后重新验证。

# 动态任务计划

本 Workflow 不把任何子环节标记为 Manager 层面的 `conditional step`。

Manager 只根据用户任务范围与 planning index 写出初始计划，不负责根据体系科学特征提前判断 1.4、1.6、1.7 或其他 Step 是否实际需要。

Task Execution Agent 在执行过程中根据：

- 当前及前序子环节的正式结果；
- 当前相关 Step Skill 的科学规则；
- 用户在当前执行对话中的明确要求；

直接增删、替换或调整尚未执行的后续子环节。

确认不需要的未执行环节直接从 Task Sheet 删除，不写 `NOT_APPLICABLE` / `SKIP` 状态，也不生成 route revision。

已经实际执行过并形成任务历史的环节不得为了整理计划而静默删除。

# 复用边界

本 Workflow 不定义通用 reuse conditions。

每个子环节真正开始时，由 Task Execution Agent：

1. 读取当前子环节 Skill；
2. 在 `project_result_index.md` 中检索该环节已有正式结果；
3. 按当前 Skill 定义的 reuse conditions 判断是否等价；
4. 明确等价则自动复用；明确不等价则正常执行；信息不足时询问用户；用户明确要求重做时跳过自动复用；
5. 只有确定需要执行时才创建当前任务的 `<base_work_directory>/<task_id>/`。

本 Workflow 不因为“同一阶段已有文件”就判定可以复用。

# 结果与记录

具体子环节 Skill 定义自己的 `official results`。

子环节完成或复用后，由 Task Execution Agent：

- 更新当前 `Txxxx.md` 中该子环节的状态、对象、工作目录、主要结果和必要执行记录；
- 将该子环节定义的正式结果登记到 `project_result_index.md`；
- 根据结果调整后续任务计划。

如果当前任务是通过复用已有结果完成该环节，`主要结果` 可以直接指向来源任务的正式结果；本任务不需要复制文件或创建空目录。

本 Workflow 自身不生成额外 route、decision、event、artifact registry 或 closure record。

# Legacy

以下旧接口已经冻结，不属于 Lightweight Runtime v2 的普通执行路径：

- Workstream-local route fragment planning；
- one-decision execution interface；
- `workflow_route_fragment.schema.yaml`；
- `workflow_decision.schema.yaml`；
- active route progression；
- route revision signal；
- runtime projection 驱动的 Workflow dispatch。

Legacy 材料仍可保留用于历史、旧项目迁移或明确的 Legacy 维护，但不得在普通 Task Execution 中加载它们。

# 自检

- [ ] 当前任务由 `Txxxx.md` 定位，而不是 Workstream / active route；
- [ ] 只为当前子环节解析实际 Skill；
- [ ] 未预读未来子环节的业务 Skill；
- [ ] Manager 只记录任务专属目录路径，未创建 `Txxxx/` 执行目录；
- [ ] 当前任务目录只在确实需要执行该子环节时由 Task Execution Agent 创建；
- [ ] 未重新定义具体子环节的科学算法、reuse conditions 或 official results；
- [ ] 未设置 Manager conditional/applicability metadata；
- [ ] 后续计划根据实际执行证据动态调整，而不是生成 SKIP / route revision；
- [ ] 未创建 Workflow decision、route fragment、event 或 runtime task；
- [ ] 未要求普通子环节结束后返回 Manager；
- [ ] 最终结构准备完成仍以 1.9 的实际验证结果为依据。
