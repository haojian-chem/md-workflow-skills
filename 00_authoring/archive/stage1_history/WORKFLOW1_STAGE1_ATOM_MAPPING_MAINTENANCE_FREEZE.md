# Workflow 1 / Stage 1 atom mapping maintenance architecture freeze

Status: **FROZEN AUTHORING RECORD — RUNTIME RULE MATERIALIZED**

Current shared runtime authority:

```text
references/atom_mapping_rules.md
```

本文件冻结 Stage 1 内部 chained atom map 的已确认架构与稳定接口。执行 Agent 日常运行读取 `references/atom_mapping_rules.md`；本 freeze 用于 authoring 追溯，不维护一套与 runtime reference 独立漂移的第二规范。

## 1. Scope and ownership

当前 atom-map chain 由以下 active Steps 维护：

```text
1.3  初始化 target atom map
1.4  copy + update
1.6  copy + update
1.7  copy + update
1.8  copy + update → stage1_final_map.yaml
```

1.5 不修改结构，不维护 map。

1.9 只读消费最终 map 做验证，不属于本次 map producer 修改授权范围。

1.2 只提供原始结构及 `component_id + residue_id` residue identity，不建立 atom map，也不读取 atom-mapping shared reference。

本 freeze 只规定 Stage 1；Stage 2 的 atom mapping / provenance 不在本次授权和本文件范围内。

## 2. Baseline and chain model

Stage 1 不建立永久 `atom_id`。

1.3 以：

```text
1.2 实际检查的原始结构
+ 1.2 classification_result.yaml 中的 component_id + residue_id
```

初始化每个 target 的第一份 atom map。

之后 1.4、1.6、1.7、1.8 都必须：

```text
当前输入结构
+ 与该输入结构对应的最近正式 atom map
→ copy input map
→ 只按当前 Step 的实际结构操作更新 copy
→ 输出与当前输出结构对应的新 map
```

不得在后续 Step 绕过 input map、根据当前结构重新猜测 `original_atom_serial`、`component_id + residue_id` 或既有 operation history。

某个结构改写 Step 未实际执行时，下一个 producer 直接使用与其当前输入结构对应的最近正式 map。

## 3. Frozen map result fields

每份 map 只记录当前输出结构中实际存在的 `ATOM / HETATM` atoms。删除 atom 不在新 map 中保留 tombstone record。

文件级固定字段：

```text
target_id
original_structure
input_structure
current_structure
input_map
atoms
```

字段含义：

- `target_id`：当前 map 所属 target 的正式标识；
- `original_structure`：当前 map chain 所追溯的原始结构文件完整绝对路径，即 1.2 实际检查的结构；
- `input_structure`：生成当前 map 时对应处理步骤的输入结构文件完整绝对路径；
- `current_structure`：当前 map 实际描述的输出结构文件完整绝对路径；
- `input_map`：生成当前 map 时所复制的上一份正式 atom map 完整绝对路径；1.3 初始化 map 时为 `null`；
- `atoms`：`current_structure` 中实际存在的 `ATOM / HETATM` 原子的逐原子记录列表。

每个 `atoms[]` record 固定保存：

```text
current_atom_serial
original_atom_serial
component_id
residue_id
operations
```

字段含义：

- `current_atom_serial`：该 atom 在 `current_structure` 中的 PDB atom serial；
- `original_atom_serial`：该 atom 在 `original_structure` 中对应 atom 的 PDB atom serial；原始结构中不存在对应 atom 时为 `null`；
- `component_id`：该 atom 所属 residue 对应的 1.2 正式 `component_id`；
- `residue_id`：该 atom 所属 residue 对应的 1.2 正式 `residue_id`，与 `component_id` 共同定位该 residue；
- `operations`：该 atom 在当前 Stage 1 map chain 中已经发生并被记录的 Step-specific atom operation code，按实际发生顺序排列。

## 4. Frozen copy-and-update behavior

后续 producer 的稳定维护逻辑冻结为：

- 删除 atom → 从输出 map 删除对应 record；
- surviving atom → 保留 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`，按输出结构更新 `current_atom_serial`；
- 当前 Step 修改 surviving atom → 在既有 `operations` 末尾追加对应 Step-specific code；
- 当前 Step 真正新增、输入结构不存在对应 atom → 新建 record，`original_atom_serial: null`；
- replacement 中输入/输出能够明确判定为同一个 atom → 保留原 record 与原始 provenance，并记录 replacement operation；
- replacement output 在输入结构中确实不存在对应 atom → 才作为新增 atom；
- 后续 Step 不得删除、重排或改写已有 operation history；
- `original_atom_serial` 一旦为非空值不得被后续 Step 改写；
- `component_id + residue_id` 不因 chain、resid、residue name、atom name、atom order 或 serial 的表示变化而重建；
- 单纯 serial 重编号不建立独立 operation code；
- 每份输出 map 与对应输出结构的 `ATOM / HETATM` 必须一一对应。

删除历史通过相邻正式 map 的差异与对应 Step 正式处理报告追溯，不在当前 map 中保留已不存在的 atom record。

## 5. Frozen operation codes

当前 Stage 1 map 固定使用：

```text
1.3ADD
1.4ALTLOC
1.6ADD
1.6RENAME
1.6REPLACE
1.7RENAME
1.8REORDER
```

冻结含义：

- `1.3ADD`：1.3 将原始结构 atom 纳入当前 target 并初始化 map record；`original_atom_serial` 必须非空；
- `1.4ALTLOC`：1.4 对 surviving selected-conformer atom 实际清除 altLoc 表示；
- `1.6ADD`：1.6 新增输入结构中不存在对应 atom 的 atom；`original_atom_serial: null`；
- `1.6RENAME`：1.6 修改 atom name；
- `1.6REPLACE`：1.6 执行 whole-residue / coordinate replacement，但输入与输出能够明确判定为同一个 atom，因此继续保留原 `original_atom_serial`；
- `1.7RENAME`：1.7 修改 atom 所属 residue name；
- `1.8REORDER`：1.8 block / residue organization 改变 atom-record 写出位置。

同一 atom 在同一步骤实际经历多个已定义操作时，按真实执行顺序追加多个 code。

新增其它 Stage 1 atom-map operation code 属于对本冻结接口的扩展，必须先重新确认并更新 shared runtime reference / freeze，不能由单个 Step 临时自造 code。

## 6. Step-specific frozen behavior

### 1.3

1.3 无 input map；对实际进入 target PDB 的每个原始 atom 建立 record：

```text
current_atom_serial = target PDB serial
original_atom_serial = original structure serial
component_id + residue_id = 1.2 formal residue identity
operations = [1.3ADD]
```

未选择 atom 不进入该 target map；selected missing residue 当前没有坐标时不建立 atom record。

### 1.4

复制 input map：删除 unselected conformer records；shared atoms 保留 history；surviving selected-conformer atoms 在实际清除 altLoc 时追加 `1.4ALTLOC`；serial 重编号只更新 `current_atom_serial`。

### 1.6

复制 input map后按 repair 实际结果维护：

- extra atom deletion → 删除 record；
- atom-name correction → `1.6RENAME`；
- 真正新增 missing heavy atom / missing-residue atom → `1.6ADD` + `original_atom_serial: null`；
- whole-residue / coordinate replacement 中有明确 input → output atom correspondence → 保留原 provenance并追加 `1.6REPLACE`；
- replacement output 没有 input counterpart → `1.6ADD`；
- replacement 后没有 output counterpart 的 input atom → 删除 record。

不得因为 coordinates 来自 reference 就把仍有明确 input counterpart 的 atom 全部降格为新增 atom。

### 1.7

复制 input map；atom set 不变。只有 residue name 实际发生变化的 residue，其全部 atom records 追加 `1.7RENAME`；其它 records 只保持/更新当前 serial。

### 1.8

复制 input map；不增删 atom。保持原始 provenance和既有 history，按 `stage1_final.pdb` 更新 `current_atom_serial`；对实际改变 atom-record 写出位置的 atoms 追加 `1.8REORDER`，最终写出 `stage1_final_map.yaml`。

## 7. Runtime synchronization status

当前 runtime authority 已由：

```text
references/atom_mapping_rules.md
```

实现。

本次授权范围内的 active Step interfaces 已同步为 chained map 模型：

```text
1.3_chain_and_residue_selection/SKILL.md
1.4_altloc_occupancy_resolution/SKILL.md
1.6_structure_completion/SKILL.md
1.7_protein_protonation_assignment/SKILL.md
1.8_reorder_and_mapping/SKILL.md
```

其中 1.6 已明确区分 `1.6REPLACE` 与真正的 `1.6ADD`，避免 whole-residue replacement 丢失已有 atom 的原始 provenance。