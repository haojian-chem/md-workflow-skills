---
name: chain_and_residue_selection
description: 根据用户要求确定结构准备 1.3 中保留的 chain / residue 研究对象，建立当前 1.3 local targets，并为每个 target 生成对应 PDB。
---

# 目标

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

Target lineage 规则由通用 Task Execution 入口按需引入；涉及 target PDB atom set / materialization 时同时读取：

`../../references/atom_mapping_rules.md`

本 Skill 仅补充 1.3-specific 的对象、reuse、执行、validation 与 results 规则。

完成结构准备阶段 `1.3 Chain and Residue Selection`。

本步骤先确定当前 1.3 要处理的 research-object selection，为每个 local target 建立独立 target record，再生成对应 PDB，并记录新结构编号与 1.2 稳定身份的映射。1.3 同时初始化对应 atom-map chain。

# Object requirements

当前 1.3 工作项开始前需要能够定位：

- 当前 model 的 1.2 正式 `classification_result.yaml`；
- 与该结果对应、由 1.2 实际检查的当前结构；
- 用户对保留研究对象的要求。

这些正式输入可以由当前 Task Sheet 提供，也可以来自同一科研任务的前序 Task Sheet或其它明确可用的正式结果；是否可执行以这些实际输入是否已经闭合为准，不要求来源识别或分类工作必须出现在当前 Task Sheet。

1.2 结果应已完成当前 model 的分类、component / residue 层级和稳定身份物化。1.3 直接使用其中已经存在的 `component_id`、component 一级 `chain_index` 与 `residue_id`；`residue_id` 只在所属 `component_id` 内定位，因此任何正式 selection / mapping 都使用 `component_id + residue_id`。

# Reuse conditions

开始本步骤时先在 `project_result_index.md` 中检查已有 1.3 正式结果。

以下内容均等价且已有结果通过本步骤 validation 时，可以直接复用：

- 当前结构相同；
- 使用的 1.2 正式分类结果相同；
- target 数量相同；
- 每个 target 的 selected research objects 相同。

复用的 1.3 结果必须同时包含与 target PDB 对应的正式 atom map；缺少该 map 的旧结果不满足当前 1.3 结果契约。

复用已有 1.3 科学结果时，当前 Task Sheet 如仍建立自己的 1.3 local targets，按共享 target-lineage 规则创建当前 target records，并将被复用的旧 1.3 target records 记录为对应 `source_target_records`；不得因为 selection 等价就把当前 local `target_id` 与旧 target 合并成同一个对象。

信息不足无法判断时向用户确认；用户明确要求重新选择或重新生成时不复用。

# Execution rules

## 1. 确定 research-object selection

用户可以使用 source / current chain、resid、residue name 或科学描述说明研究对象；完成 grounding 后，内部 selection 统一使用 1.2 已生成的 `component_id + residue_id`。

不得重新构造这些 opaque IDs。

用户可以按完整 chain、单个 residue、residue range、不连续 residues 或其组合指定保留范围。

如果省略的信息能够依据当前上下文和 1.2 结果唯一确定，可以直接补足。例如用户写 `HEM 401`，且只有一个匹配 residue，则无需再次确认 chain。

以下情况需要向用户确认：

- 存在多个合理匹配对象；
- 用户给出的身份与 1.2 结果冲突；
- residue range 缺少 chain 且不能唯一确定；
- 指定对象不存在；
- 科学描述不能唯一映射到结构对象。

存在多个合理候选时不得静默替用户选择。

如果 selected research-object 范围包含 1.2 中 `missing_residue_check.status: ISSUE` 的 residue，该 residue 仍属于 selection，并保留对应 `component_id + residue_id`。

默认建立一个 local target。一句话中出现多个 chain / residue 不自动拆分 target；只有用户明确要求分别生成多个结构时，才建立多个 1.3 targets。

同一 target 中重复或被更大 selection 包含的 residue 去重；同一个 `component_id` 只记录一次。

## 2. 建立 1.3 target records

当前 Task Sheet 的 1.3 工作目录使用：

```text
selection_index.yaml
targets/
├── target_001.yaml
├── target_002.yaml
└── ...
structures/
├── target_001.pdb
├── target_002.pdb
└── ...
maps/
├── target_001.atom_mapping.yaml
├── target_002.atom_mapping.yaml
└── ...
```

### `selection_index.yaml`

记录当前 1.3 有哪些 local targets：

```yaml
targets:
  - target_id: target_001
    description: "A 链和 HEM"
    target_file: targets/target_001.yaml

  - target_id: target_002
    description: "B 链 100–150"
    target_file: targets/target_002.yaml
```

字段含义：

- `target_id`：当前 1.3 工作项内的 local target 编号；
- `description`：用户可读的简短说明，可使用 source identity 或科学描述；
- `target_file`：当前 1.3 target record 相对路径。

`description` 仅用于阅读，不作为后续重新解析 selection 或跨 Skill identity 的依据。

### `targets/target_xxx.yaml`

每个 1.3 local target 使用一个独立 YAML，并作为该 target 的正式 `target_record`。

新执行的 1.3 selection 是当前 target lineage 的起点，因此：

```yaml
target_id: target_001
source_target_records: []
description: "A 链和 HEM"

selections:
  - component_id: <component_id>
    residue_ids:
      - <residue_id>
      - <residue_id>

  - component_id: <component_id>
    residue_ids:
      - <residue_id>
```

其中：

- `source_target_records: []` 表示当前 1.3 target 没有上游 target；
- `selections` 是当前 1.3 target 的 research-object selection；
- `component_id` 和 `residue_id` 直接使用当前 model 的 1.2 正式 identity；
- `residue_ids` 只在其所属 `component_id` 下解释；
- `residue_ids` 表示 membership，不表示 residue 输出顺序；
- selected missing residue 同样记录在 `residue_ids` 中。

如果当前 1.3 local target 是对已有 1.3 正式结果的复用投影，而不是新 selection 起点，则 `source_target_records` 记录实际复用的旧 target record；此时当前 target record 仍是新的 local target record。

生成 PDB 与 atom map 后，在同一 target record 中补充：

```yaml
structure: /absolute/path/to/structures/target_001.pdb
atom_mapping: /absolute/path/to/maps/target_001.atom_mapping.yaml

chain_mapping:
  - chain_index: 1
    pdb_chain_id: A

residue_mapping:
  - chain_index: 1
    resid: 1
    component_id: <component_id>
    residue_id: <residue_id>

  - chain_index: 1
    resid: 2
    component_id: <component_id>
    residue_id: <residue_id>
```

这里的 `chain_index` 直接使用当前 model 的 1.2 component 一级 `chain_index`，不在 1.3 重新计算。

`chain_mapping` 记录当前 target 输出 PDB 的 `chain_index` 与 PDB chain ID；`residue_mapping` 记录输出结构 `chain_index + resid` 与 1.2 `component_id + residue_id` 的关系。

selected missing residue 即使没有坐标，也保留对应 `residue_mapping`；由于当前没有 atom record，因此不会在 1.3 atom map 中生成 atom entry。

需要对象的 missing、classification、heavy-atom、conformation 等信息时，通过 `component_id + residue_id` 查询 1.2 `components[].residues[]` 中的正式结果，不在 target record 重复记录。

## 3. 生成 PDB

每个 current target 生成：

```text
structures/target_xxx.pdb
```

具体生成规则见：

`references/pdb_materialization_rules.md`

## 4. 初始化 atom map

每个 current target 同时生成：

```text
maps/target_xxx.atom_mapping.yaml
```

1.3 按 `../../references/atom_mapping_rules.md` 初始化 map：

- `target_record` 指向当前 `targets/target_xxx.yaml` 的完整绝对路径；
- `original_structure` 与 `input_structure` 均指向本次 1.2 实际检查的结构；
- `current_structure` 指向当前 target PDB；
- `input_map: null`；
- 每个实际写入 target PDB 的 atom 建立一条 record；
- `current_atom_serial` 使用 target PDB serial；
- `original_atom_serial` 使用该 atom 在原始结构中的 serial；
- `component_id + residue_id` 使用当前 1.2 正式 residue identity；
- `operations` 初始化为 `[1.3ADD]`。

未进入当前 target 的 atoms 不写入该 target map。

# Validation requirements

完成 target record、PDB 与 atom map 后，按：

`references/validation.md`

验证 selection、PDB organization 和 mapping，并额外确认：

- 每个 current target 都有唯一 `targets/target_xxx.yaml`；
- target record 的 `target_id` 与当前 1.3 local target 一致；
- 新 selection target 的 `source_target_records` 为空；复用投影 target 的 source 关系与实际复用来源一致；
- target PDB 中每个 `ATOM / HETATM` 恰有一条 atom-map record；
- atom map 不存在 target PDB 中没有的额外 atom record；
- atom map `target_record` 指向当前 target record；
- 每条 map record 的 `current_atom_serial`、`original_atom_serial`、`component_id + residue_id` 与当前 target / 原始结构能够唯一对应；
- 每条 1.3 初始化 record 的 `operations` 含 `1.3ADD`。

验证未通过时当前 1.3 保持未完成。

# Official results

当前 Step 的正式结果包括：

- `selection_index.yaml`；
- `targets/target_*.yaml`；
- `structures/target_*.pdb`；
- `maps/target_*.atom_mapping.yaml`；
- `selection_validation.md`。

其中 `targets/target_*.yaml` 同时承担当前 1.3 local target 的 target record；后续 Skill 引用 target 时使用其完整绝对路径，不通过 `target_id` 编号相同建立对应关系。

项目级正式结果索引：

```text
<project_root>/00_project_records/project_result_index.md
```

只登记 `selection_index.yaml` 的完整绝对路径及简明说明。具体 target record 继续定位对应 PDB 与 atom map；这些文件与 `selection_validation.md` 不分别登记为 project-level result entry。

# 工作目录

基础目录：

```text
01_structure_preparation/03_chain_and_residue_selection/
```

当前 Task Sheet 实际执行目录：

```text
01_structure_preparation/03_chain_and_residue_selection/<task_id>/
```

这里的 `<task_id>` 是当前 Task Sheet 的 `Txxxx` 标识。

先完成 reuse 判断；只有确实需要本地执行时才创建当前 Task Sheet 的工作目录。

# Preflight

执行前确认：

- 当前对象能够定位到一个确定 model 的 1.2 正式分类结果和对应结构；
- 当前结构中的 atom serial 能够作为本次 1.3 `original_atom_serial` 唯一定位原子；
- 当前用户 selection 已能唯一 grounding，或需要的用户确认已经完成；
- 所有 selected `component_id + residue_id` 组合均来自当前 1.2 结果；
- 输出位于当前 Task Sheet 的 1.3 工作目录且不会覆盖其它 Task Sheet 或其它科研任务的正式结果。
