# Stage 1 原子映射维护共享规则

本文件定义 Stage 1 中结构改写步骤共同使用的原子映射规则。当前适用步骤为 1.3、1.4、1.6、1.7、1.8；1.5 不修改结构，因此不维护 map；1.9 读取最终 map 做验证。

本文件只规定 Stage 1，不定义 Stage 2 的 mapping / provenance 语义。

## 1. Map chain

Stage 1 使用一条随当前 target 结构持续维护的 atom map。

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

某个步骤未实际执行时，下一个结构改写步骤直接复制与其当前输入结构对应的最近一份正式 map。

1.3 是 map chain 的初始化步骤；1.4、1.6、1.7、1.8 均不得重新从结构猜测一套独立 mapping，而必须复制当前输入结构对应的正式 map，再根据本步骤实际结构操作维护该副本。

## 2. 固定数据结构

每份 map 只记录当前结构中实际存在的 `ATOM / HETATM` 原子。已从当前结构删除的 atom 不保留在输出 map 中。

固定文件级结构：

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

每个 atom record 固定保存：

```text
current_atom_serial
original_atom_serial
component_id
residue_id
operations
```

字段语义：

- `current_atom_serial`：该 atom 在 `current_structure` 中的当前 PDB atom serial；
- `original_atom_serial`：该 atom 在 `original_structure` 中对应 atom 的 PDB atom serial；若该 atom 是后续步骤新增、原始结构中不存在对应 atom，则为 `null`；
- `component_id + residue_id`：使用 1.2 正式结果中的 residue identity；
- `operations`：从 1.3 开始累积保留的 atom-level operation history，按实际发生顺序排列。

`original_atom_serial` 一旦为非空值，后续步骤不得改写。`component_id + residue_id` 也不得因为 chain / resid / residue name / atom serial 的表示变化而重新生成。

## 3. Copy-and-update 规则

1.4、1.6、1.7、1.8 每次维护 map 时按以下顺序执行：

1. 完整复制与当前输入结构对应的正式 input map；
2. 对本步骤删除的 atom，删除对应 atom record；
3. 对 surviving atom，按输出结构更新 `current_atom_serial`；
4. 对本步骤实际修改的 surviving atom，在原 `operations` 列表末尾追加当前步骤 operation code；
5. 对本步骤新增的 atom，新建 atom record，`original_atom_serial: null`，并写入当前步骤的 `ADD` operation；
6. 不删除、不改写 input map 中已经存在的历史 operation；
7. 写出后，输出 map 的 atom records 必须与当前输出结构中的 `ATOM / HETATM` 一一对应。

单纯 atom serial 重编号不单独追加 operation code；serial 的跨步骤变化由相邻两份 map 的 `current_atom_serial` 自然体现。

## 4. Operation code

`operations` 使用带 Step 编号的 operation code，使最终 map 能直接看出 atom 在 Stage 1 中经历过哪些实际结构处理。

当前固定使用：

```text
1.3ADD
1.4ALTLOC
1.6ADD
1.6RENAME
1.7RENAME
1.8REORDER
```

语义：

- `1.3ADD`：1.3 将原始结构中的该 atom 纳入当前 target，并初始化其 map record；此时 `original_atom_serial` 必须非空；
- `1.4ALTLOC`：该 surviving atom 属于 1.4 已解析的 alternate-conformation object，并发生了 surviving altLoc 表示清除；
- `1.6ADD`：该 atom 由 1.6 新增，包括 missing heavy atom、missing residue 或 whole-residue replacement 新写入的 atom；`original_atom_serial` 必须为 `null`；
- `1.6RENAME`：1.6 修改了该 atom 的 atom name；
- `1.7RENAME`：1.7 修改了该 atom 所属 residue 的 residue name；
- `1.8REORDER`：1.8 的 block / residue organization 改变了该 atom 相对于其它 atoms 的写出位置。

删除 atom 不在输出 map 中保留 `REMOVE` record；删除事实由 input map 与 output map 的差异以及当前步骤正式结构处理报告共同追溯。

如果后续 Stage 1 Skill 新增其它会改变 atom identity / representation 的操作，需要在本共享规则中先定义新的 Step-specific operation code，再由对应 Skill 使用。

## 5. 1.3 初始化

1.3 不存在 input map。

对每个 target：

- 以 1.2 所检查的原始结构作为 `original_structure`；
- 对实际写入 target PDB 的每个 source atom 建立一个 map record；
- `original_atom_serial` 取该 atom 在原始结构中的 serial；
- `current_atom_serial` 取 1.3 target PDB 中的新 serial；
- `component_id + residue_id` 取 1.2 正式 residue identity；
- `operations` 初始化为 `[1.3ADD]`；
- 未被当前 target 选择的 atom 不进入该 target 的 map；
- selected missing residue 尚无 atom coordinates，因此不产生 atom record，待 1.6 实际新增 atom 时再建立 record。

1.3 输出 target PDB 与该 target 的 atom map 必须一一对应。

## 6. 1.4 维护

1.4 从 1.3 或最近上游结构改写步骤复制 input map。

- unselected-conformer atom 从输出 map 删除；
- shared atom 直接保留原 history；
- surviving selected-conformer atom 保留 `original_atom_serial`、`component_id + residue_id`，更新 `current_atom_serial`；
- 对实际清除 surviving altLoc 的 atom 追加 `1.4ALTLOC`；
- serial 重编号本身不追加 operation。

## 7. 1.6 维护

1.6 从与 `structure_completeness_report.yaml.structure` 对应的最近正式 atom map 复制并更新。

- confirmed extra atom 删除 → 删除对应 record；
- atom-name correction → 保留对应 record，更新 current serial，并追加 `1.6RENAME`；
- missing heavy atom 新增 → 新建 record，`original_atom_serial: null`，`operations: [1.6ADD]`；
- missing residue 新增 → 该 residue 的所有新增 atoms 均建立新 record，`original_atom_serial: null`，`operations: [1.6ADD]`；
- whole-residue replacement → 被删除的原 partial-residue atom records 删除；replacement atoms 作为新 atoms 建立 record，并使用 `1.6ADD`；
- 未被本步骤修改的 surviving atoms 保留原 history，只更新当前 serial。

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
- 对因 1.8 block / residue organization 而实际改变相对写出位置的 atoms 追加 `1.8REORDER`；
- 最终正式 map 文件名保持：

```text
stage1_final_map.yaml
```

`stage1_final_map.yaml` 使用本文件规定的同一数据结构，不另建第二套 final-map schema。

## 10. Map validation

每个生成 map 的步骤至少确认：

- 当前输出结构每个 `ATOM / HETATM` atom 恰有一个 map record；
- map 不存在当前结构中没有的额外 atom record；
- `current_atom_serial` 在当前结构中唯一且可定位；
- `component_id + residue_id` 能定位到当前 model 的 1.2 正式 residue；
- 对 `original_atom_serial != null` 的 record，该 serial 能定位到 `original_structure` 中唯一 atom；
- 对 `original_atom_serial == null` 的 record，history 中必须存在使该 atom进入结构的后续 `ADD` operation；
- copy-and-update 没有丢失或重写既有 operation history；
- 当前步骤新增的 operation 与本步骤实际结构修改一致。

1.9 对 `stage1_final.pdb` 与 `stage1_final_map.yaml` 重复执行上述最终一致性检查，但不修改 map。
