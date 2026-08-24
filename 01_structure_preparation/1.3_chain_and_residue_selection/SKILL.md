---
name: chain_and_residue_selection
description: 根据用户要求确定结构准备 1.3 中保留的 chain / residue 研究对象，记录 target，并为每个 target 生成对应 PDB。
---

# 目标

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 仅补充 1.3-specific 的对象、reuse、执行、validation 与 results 规则。

完成结构准备阶段 `1.3 Chain and Residue Selection`。

本步骤先确定后续研究实际保留的研究对象，再为每个 target 生成对应 PDB，并记录新结构编号与 1.2 稳定身份的映射。

# Object requirements

当前任务需要明确提供：

- 当前 model 的 1.2 正式 `classification_result.yaml`；
- 与该结果对应的当前结构；
- 用户对保留研究对象的要求。

1.2 结果应已完成当前 model 的分类、component / residue 层级和稳定身份物化。1.3 直接使用其中已经存在的 `component_id` 与 `residue_id`；`residue_id` 只在所属 `component_id` 内定位，因此任何正式 selection / mapping 都使用 `component_id + residue_id`。

# Reuse conditions

开始本步骤时先在 `project_result_index.md` 中检查已有 1.3 正式结果。

以下内容均等价且已有结果通过本步骤 validation 时，可以直接复用：

- 当前结构相同；
- 使用的 1.2 正式分类结果相同；
- target 数量相同；
- 每个 target 的 selected research objects 相同。

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

默认建立一个 target。一句话中出现多个 chain / residue 不自动拆分 target；只有用户明确要求分别生成多个结构时，才建立多个 target。

同一 target 中重复或被更大 selection 包含的 residue 去重；同一个 `component_id` 只记录一次。

## 2. 记录 selection

当前任务目录使用：

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
```

### `selection_index.yaml`

记录当前有哪些 target：

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

- `target_id`：当前 1.3 内的 target 编号，使用 `target_001`、`target_002`……；
- `description`：用户可读的简短说明，可使用 source identity 或科学描述；
- `target_file`：对应 target 记录文件。

`description` 仅用于阅读，不作为后续重新解析 selection 的依据。

### `targets/target_xxx.yaml`

每个 target 使用一个独立 YAML。确定 selection 后记录：

```yaml
target_id: target_001

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

- `selections` 是该 target 的 research-object selection；
- `component_id` 和 `residue_id` 直接使用当前 model 的 1.2 正式 identity；
- `residue_ids` 只在其所属 `component_id` 下解释；
- `residue_ids` 表示 membership，不表示 residue 输出顺序；
- selected missing residue 同样记录在 `residue_ids` 中。

生成 PDB 后，在同一文件中补充：

```yaml
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

这里的 `chain_index` 是 1.3 为当前 target 输出结构建立的 mapping 编号，不是从 1.2 继承的 identity。

`chain_mapping` 记录当前 target 输出 PDB 的 `chain_index` 与 PDB chain ID；`residue_mapping` 记录输出结构 `chain_index + resid` 与 1.2 `component_id + residue_id` 的关系。

selected missing residue 即使没有坐标，也保留对应 `residue_mapping`。

需要对象的 missing、classification、heavy-atom、conformation 等信息时，通过 `component_id + residue_id` 查询 1.2 `components[].residues[]` 中的正式结果，不在 target 文件重复记录。

## 3. 生成 PDB

每个 target 生成：

```text
structures/target_xxx.pdb
```

具体生成规则见：

`references/pdb_materialization_rules.md`

# Validation requirements

完成 target 记录和 PDB 生成后，按：

`references/validation.md`

验证 selection、PDB organization 和 mapping。验证未通过时当前 1.3 保持未完成。

# Official results

当前 Step 的正式结果包括：

- `selection_index.yaml`；
- `targets/target_*.yaml`；
- `structures/target_*.pdb`；
- `selection_validation.md`。

项目级正式结果索引：

```text
<project_root>/00_project_records/project_result_index.md
```

只登记 `selection_index.yaml` 的完整绝对路径及简明说明。`targets/target_*.yaml`、`structures/target_*.pdb` 与 `selection_validation.md` 保持为当前 Step 的正式结果，但不分别登记为 project-level result entry；需要具体 target 时由 `selection_index.yaml` 继续定位。

# 工作目录

基础目录：

```text
01_structure_preparation/03_chain_and_residue_selection/
```

当前任务实际执行目录：

```text
01_structure_preparation/03_chain_and_residue_selection/<task_id>/
```

先完成 reuse 判断；只有确实需要本地执行时才创建当前任务目录。

# Preflight

执行前确认：

- 当前对象能够定位到一个确定 model 的 1.2 正式分类结果和对应结构；
- 当前用户 selection 已能唯一 grounding，或需要的用户确认已经完成；
- 所有 selected `component_id + residue_id` 组合均来自当前 1.2 结果；
- 输出位于当前任务目录且不会覆盖其他任务正式结果。
