# 原子映射维护共享规则

本文件定义当前适用结构改写环节共同使用的原子映射规则。Stage 1 当前适用步骤为 1.3、1.4、1.6、1.7、1.8；1.5 不修改结构，因此不维护 map；1.9 读取最终 map 做验证。

标准残基拓扑生成过程中沿用本文件的 map 结果结构、copy-and-update 语义和 provenance 维护规则，并使用 `2.2ADD` 记录该环节新增的 atom。本文件当前不定义其它 Stage 2 环节的 mapping / provenance 语义。

## 1. Map chain

Stage 1 使用一条随当前 target 结构持续维护的 atom map：

```text
1.2 所检查的原始结构
↓
1.3 初始化 target atom map
↓
1.4 copy + update
↓
1.6 copy + update
↓
1.7 copy + update
↓
1.8 copy + update → stage1_final_map.yaml
```

某个步骤未实际执行时，下一个结构改写步骤直接使用与其当前输入结构对应的最近一份正式 map。

1.3 是 map chain 的初始化步骤；1.4、1.6、1.7、1.8 均不得绕过当前输入 map、再从结构重新猜测一套独立 mapping。每一步都先复制与输入结构对应的正式 map，再依据本步骤实际结构操作维护该副本。

Stage 1 不额外建立永久 `atom_id`。

## 2. Map 结果结构与字段含义

每份 map 只记录 `current_structure` 中实际存在的 atom。已经从当前结构删除的 atom 不保留在当前输出 map 中。

固定结果结构：

```yaml
target_id: target_001
original_structure: /absolute/path/to/structure_checked_by_1.2.pdb
input_structure: /absolute/path/to/current_step_input.pdb
current_structure: /absolute/path/to/current_step_output.pdb
input_map: /absolute/path/to/input_atom_mapping.yaml  # 1.3 为 null

atoms:
  - current_atom_serial: 1
    original_atom_serial: 125
    component_id: component_001
    residue_id: residue_001
    operations:
      - 1.3ADD
```

文件级字段含义：

- `target_id`：当前 map 所属 target 的正式标识；
- `original_structure`：当前 map chain 所追溯的原始结构文件完整绝对路径，即 1.2 实际检查的结构；
- `input_structure`：生成当前 map 时所对应处理步骤的输入结构文件完整绝对路径；
- `current_structure`：当前 map 实际描述的输出结构文件完整绝对路径；
- `input_map`：生成当前 map 时所复制的上一份正式 atom map 完整绝对路径；1.3 初始化 map 时为 `null`；
- `atoms`：`current_structure` 中实际存在的 atom 的逐原子记录列表。

每个 `atoms[]` record 固定保存：

```text
current_atom_serial
original_atom_serial
component_id
residue_id
operations
```

字段含义：

- `current_atom_serial`：该 atom 在 `current_structure` 中的 atom serial；
- `original_atom_serial`：该 atom 在 `original_structure` 中对应 atom 的 PDB atom serial；如果 `original_structure` 中不存在对应 atom，则为 `null`；
- `component_id`：该 atom 所属 residue 对应的 1.2 正式 `component_id`；
- `residue_id`：该 atom 所属 residue 对应的 1.2 正式 `residue_id`，与 `component_id` 共同定位该 residue；
- `operations`：该 atom 在当前 map chain 中已经发生并被记录的 atom-level operation code，按实际发生顺序排列。

## 3. Copy-and-update 规则

1.4、1.6、1.7、1.8 以及采用本规则的后续结构改写环节，每次维护 map 时按以下顺序执行：

1. 完整复制与当前输入结构对应的正式 input map；
2. 对本步骤删除的 atom，删除对应 atom record；
3. 对 surviving atom，按输出结构更新 `current_atom_serial`；
4. 对本步骤实际修改的 surviving atom，在原 `operations` 列表末尾追加对应的 Step-specific operation code；
5. 对本步骤新增、且输入结构不存在对应 atom 的 atom，新建 atom record，`original_atom_serial: null`，并写入当前步骤的 `ADD` operation；
6. 对本步骤发生 replacement、但输入与输出能够明确判定为同一个 atom 的情况，保留原 record 及其 `original_atom_serial`，追加当前步骤的 replacement operation；
7. 不删除、不改写 input map 中已经存在的 operation history；
8. 写出后，输出 map 的 atom records 必须与当前输出结构中的 atom 一一对应。

`original_atom_serial` 一旦为非空值，后续步骤不得改写。`component_id + residue_id` 也不得因为 chain、resid、residue name、atom name、atom order 或 atom serial 的表示变化而重新生成。

单纯 atom serial 重编号不单独追加 operation code；serial 的跨步骤变化由相邻两份 map 的 `current_atom_serial` 自然体现。

删除 atom 不在当前输出 map 中保留 tombstone / REMOVE record。删除事实由 input map 与 output map 的差异以及当前步骤正式结构处理报告共同追溯。

## 4. Operation code

`operations` 使用带 Step 编号的 operation code。当前固定使用：

```text
1.3ADD
1.4ALTLOC
1.6ADD
1.6RENAME
1.6REPLACE
1.7RENAME
1.8REORDER
2.2ADD
```

语义：

- `1.3ADD`：1.3 将原始结构中的该 atom 纳入当前 target 并初始化其 map record；此时 `original_atom_serial` 必须非空；
- `1.4ALTLOC`：该 surviving atom 属于 1.4 已解析的 alternate-conformation object，并实际发生 surviving altLoc 表示清除；
- `1.6ADD`：该 atom 由 1.6 新增，输入结构中不存在对应 atom；`original_atom_serial` 必须为 `null`；
- `1.6RENAME`：1.6 修改了该 atom 的 atom name；
- `1.6REPLACE`：1.6 对该 atom 执行 whole-residue replacement / coordinate replacement，但输入 atom 与输出 atom 能够明确判定为同一个 atom，因此保留原映射与 `original_atom_serial`；
- `1.7RENAME`：1.7 修改了该 atom 所属 residue 的 residue name；
- `1.8REORDER`：1.8 的 block / residue organization 改变了该 atom 在输出 atom records 中的位置；
- `2.2ADD`：该 atom 由标准残基拓扑生成过程中的 pdb2gmx 处理新增，输入结构中不存在对应 atom；`original_atom_serial` 必须为 `null`。

同一个 atom 在同一步骤实际经历多个已定义操作时，按实际发生顺序追加多个 operation code。

如果后续当前适用范围内的 Skill 新增其它会改变 atom identity / representation、且需要进入累积 map history 的操作，必须先在本共享规则中定义新的 Step-specific operation code，再由对应 Skill 使用。

## 5. 1.3 初始化

1.3 不存在 input map。

对每个 target：

- 以 1.2 实际检查的结构作为 `original_structure` 和 `input_structure`；
- `input_map: null`；
- 对实际写入 target PDB 的每个 source atom 建立一个 map record；
- `original_atom_serial` 取该 atom 在原始结构中的 serial；
- `current_atom_serial` 取 1.3 target PDB 中的新 serial；
- `component_id + residue_id` 取 1.2 正式 residue identity；
- `operations` 初始化为 `[1.3ADD]`；
- 未被当前 target 选择的 atom 不进入该 target 的 map；
- selected missing residue 尚无 atom coordinates，因此不产生 atom record，待后续步骤实际新增 atom 时再建立 record。

1.3 输出 target PDB 与该 target 的 atom map 必须一一对应。

## 6. 1.4 维护

1.4 复制与其输入结构对应的正式 map。

- unselected-conformer atom 从输出 map 删除；
- shared atom 直接保留原 history；
- surviving selected-conformer atom 保留 `original_atom_serial`、`component_id + residue_id`，按输出 PDB 更新 `current_atom_serial`；
- 对实际清除 surviving altLoc 的 atom 追加 `1.4ALTLOC`；
- serial 重编号本身不追加 operation。

## 7. 1.6 维护

1.6 复制与 `structure_completeness_report.yaml.structure` 对应的最近正式 atom map，并按实际 repair 结果更新。

- confirmed extra atom 删除 → 删除对应 record；
- atom-name correction → 保留对应 record 与 provenance，追加 `1.6RENAME`；
- missing heavy atom 新增 → 新建 record，`original_atom_serial: null`，`operations` 以 `1.6ADD` 记录该新增；
- missing residue 新增 → 该 residue 的所有新增 atoms 均建立新 record，`original_atom_serial: null`，以 `1.6ADD` 记录；
- whole-residue replacement / coordinate replacement：
  - 输入与输出能够通过 `component_id + residue_id` 及 atom correspondence 明确判定为同一个 atom → 保留输入 record、保留 `original_atom_serial` 和既有 history，并追加 `1.6REPLACE`；
  - 输出 atom 在输入结构中确实不存在对应 atom → 作为新增 atom 建立 record，`original_atom_serial: null`，追加 `1.6ADD`；
  - 输入 atom 在 replacement 后不再存在对应输出 atom → 从输出 map 删除；
- 未被本步骤修改的 surviving atoms 保留原 history，只更新当前 serial。

不得因为 whole-residue replacement 使用了 reference coordinates，就把仍可明确对应到输入 atom 的所有原子统一改写成 `original_atom_serial: null`。

## 8. 1.7 维护

1.7 复制与其输入 heavy-atom structure 对应的正式 map。

1.7 不改变 atom set、atom name、coordinates 或 atom order：

- 所有 atom records 保留；
- `original_atom_serial`、`component_id + residue_id` 保持不变；
- `current_atom_serial` 与输出结构保持一致；
- 对 residue name 实际发生修改的 residue，其全部 atom records 追加 `1.7RENAME`；
- residue name 未发生变化的 residue 不追加 operation。

## 9. 1.8 维护与最终 map

1.8 复制与其输入 heavy-atom structure 对应的正式 map，并据最终 `stage1_final.pdb` 更新。

- 不新增或删除 atom record；
- 保持所有 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`；
- 按最终 PDB 更新 `current_atom_serial`；
- 对因 1.8 block / residue organization 而实际改变 atom-record 写出位置的 atoms 追加 `1.8REORDER`；
- 最终正式 map 文件名保持：

```text
stage1_final_map.yaml
```

`stage1_final_map.yaml` 使用本文件规定的同一数据结构，不另建第二套 final-map schema。

## 10. 2.2 维护

生成标准残基全原子结构时，以与当前体系 `stage1_final.pdb` 对应的 `stage1_final_map.yaml` 作为上游 map source。

先按当前处理范围保留进入 pdb2gmx 输入 PDB 的标准残基 atom records，再依据 pdb2gmx 实际输出维护 map：

- 不属于当前处理范围的 atom records 不进入 `standard.map`；
- `stage1_final_map.yaml` 中对应、且在 `standard.gro` 中仍有明确对应的 atom，保留 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`，并按 `standard.gro` 更新 `current_atom_serial`；
- pdb2gmx 新增、且输入结构中不存在对应 atom 的 atom，新建 record，`original_atom_serial: null`，`component_id + residue_id` 取其所属 residue 的既有身份，`operations` 记录 `2.2ADD`；
- `input_structure` 指向本次实际使用的 pdb2gmx 输入 PDB；
- `input_map` 指向实际使用的 `stage1_final_map.yaml`；
- `current_structure` 指向 `standard.gro`；
- 输出 map basename 固定为 `standard.map`。

本环节不建立第二套 atom identity，也不根据输出 atom name、resid、chain 或 atom order 重建 `component_id + residue_id`。

## 11. Map validation

每个生成 map 的步骤至少确认：

- 当前输出结构每个 atom 恰有一个 map record；
- map 不存在当前结构中没有的额外 atom record；
- `current_atom_serial` 在当前结构中唯一且可定位；
- `component_id + residue_id` 能定位到当前 model 的 1.2 正式 residue；
- 对 `original_atom_serial != null` 的 record，该 serial 能定位到 `original_structure` 中唯一 atom；
- 对 `original_atom_serial == null` 的 record，history 中必须存在使该 atom 进入结构的后续 `ADD` operation；
- copy-and-update 没有丢失或重写既有 operation history；
- 当前步骤新增的 operation 与本步骤实际结构修改一致；
- `1.6REPLACE` 只能用于输入/输出 atom correspondence 已明确的 replacement atom，不得用于实际新增 atom。

1.9 对 `stage1_final.pdb` 与 `stage1_final_map.yaml` 重复执行上述最终一致性检查，但不修改 map。