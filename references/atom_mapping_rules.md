# 原子映射维护共享规则

本文件定义当前适用结构改写环节共同使用的原子映射规则。Stage 1 当前适用步骤为 1.3、1.4、1.6、1.7、1.8；1.5 不修改结构，因此不维护 map；1.9 读取最终 map 做验证。

标准残基拓扑生成过程中沿用本文件的 map 结果结构、copy-and-update 语义和 provenance 维护规则，并使用 `2.2ADD` 记录该环节新增的 atom。拓扑整合过程中，若按已采用的拓扑定义为实际 solvent / ion residue 补入当前结构中不存在的 atom，使用 `2.5ADD` 记录该新增；除该 operation code 外，本文件当前不定义其它 Stage 2 环节的 mapping / provenance 语义。

Target 的跨 Skill 演化、分支与合流由：

`references/target_lineage_rules.md`

拥有。Atom map 只记录当前 map 所属 local target 的 `target_record`，不通过裸 `target_id` 建立跨环节 identity。

## 1. Map chain 与 target lineage

结构改写使用一条随实际结构状态更新的 atom-map chain：

```text
1.2 所检查的原始结构
↓
1.3 初始化 atom map
↓
1.4 copy + update
↓
1.6 copy + update
↓
1.7 copy + update
↓
1.8 copy + update → stage1_final_map.yaml
↓
2.2 / 2.5 等适用结构改写
```

某个不修改结构的步骤不会生成新的 map；下一个结构改写步骤使用与其实际输入结构对应的最近正式 map。

Map chain 与 target lineage 是两个互补接口：

- `input_map`：追踪当前结构直接从哪一份 atom map copy-and-update；
- `target_record`：指出当前 map 属于哪个 current local target；
- 当前 target 的上游 target 关系由该 target record 中的 `source_target_records` 追溯。

因此，中间存在 1.5 等不生成 map 的 target-based Step 时，当前 map 的 target record 不要求把 `input_map.target_record` 作为唯一直接 source target；只要求 target lineage 能正确解释当前 target 与输入结构来源之间的关系。

Stage 1 不额外建立永久 `atom_id`。

## 2. Map 结果结构与字段含义

每份 map 只记录 `current_structure` 中实际存在的 atom。已经从当前结构删除的 atom 不保留在当前输出 map 中。

固定文件级结构：

```yaml
target_record: /absolute/path/to/current/targets/target_001.yaml
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

文件级字段：

- `target_record`：当前 map 所属 local target 的 target record 完整绝对路径；
- `original_structure`：当前 map chain 所追溯的原始结构文件完整绝对路径，即 1.2 实际检查的结构；
- `input_structure`：生成当前 map 的实际输入结构完整绝对路径；
- `current_structure`：当前 map 实际描述的结构完整绝对路径；
- `input_map`：当前 map copy-and-update 的直接上游正式 map；1.3 初始化时为 `null`；
- `atoms`：`current_structure` 中实际存在 atom 的逐原子记录。

Map 文件级不再使用跨环节 `target_id`。需要当前 local `target_id` 时读取 `target_record`。

每个 `atoms[]` record 固定保存：

```text
current_atom_serial
original_atom_serial
component_id
residue_id
operations
```

字段语义：

- `current_atom_serial`：该 atom 在 `current_structure` 中的当前编号；
- `original_atom_serial`：该 atom 在 `original_structure` 中对应 atom 的 PDB atom serial；原始结构不存在该 atom 时为 `null`；
- `component_id`：该 atom 所属 residue 的 1.2 正式 `component_id`；
- `residue_id`：该 atom 所属 residue 的 1.2 正式 `residue_id`，与 `component_id` 共同定位 residue；
- `operations`：该 atom 已发生并进入 provenance 的 Step-specific operation code，按实际发生顺序排列。

## 3. Copy-and-update

1.4、1.6、1.7、1.8 以及采用本规则的后续结构改写环节，每次维护 map 时：

1. 完整复制与当前输入结构对应的正式 input map 作为逐原子 provenance 基线；
2. 将文件级 `target_record` 更新为**当前 Step 当前 local target 的 target record**；
3. `original_structure` 保持原 map chain 的原始结构；
4. `input_structure` 指向当前实际输入结构；
5. `current_structure` 指向当前实际输出结构；
6. `input_map` 指向本次实际复制的正式上游 map；
7. 对本步骤删除的 atom，删除对应 atom record；
8. 对 surviving atom，按输出结构更新 `current_atom_serial`；
9. 对本步骤实际修改的 surviving atom，在原 `operations` 末尾追加对应 operation code；
10. 对本步骤新增、输入结构中不存在对应 atom 的 atom，新建 record，`original_atom_serial: null`，并写入当前 `ADD` operation；
11. replacement 中若输入与输出能够明确判定为同一个 atom，保留原 record 和 `original_atom_serial`，追加 replacement operation；
12. 不删除、不改写 input map 中已经存在的 operation history；
13. 输出 map atom records 与当前输出结构 atom 一一对应。

`original_atom_serial` 一旦为非空值，后续不得改写。`component_id + residue_id` 也不得因为 chain、resid、residue name、atom name、atom order 或 serial 表示变化重新生成。

单纯 atom serial 重编号不单独追加 operation code。

删除 atom 不在当前输出 map 中保留 tombstone / REMOVE record。删除事实由 input map 与 output map 的差异以及当前步骤正式结构处理结果共同追溯。

## 4. Operation code

当前固定使用：

```text
1.3ADD
1.4ALTLOC
1.6ADD
1.6RENAME
1.6REPLACE
1.7RENAME
1.8REORDER
2.2ADD
2.5ADD
```

语义：

- `1.3ADD`：1.3 将原始结构中的 atom 纳入当前 1.3 target；`original_atom_serial` 必须非空；
- `1.4ALTLOC`：surviving atom 属于 1.4 已解析 alternate-conformation object，并实际清除 surviving altLoc 表示；
- `1.6ADD`：1.6 新增 atom；输入结构中无对应 atom，`original_atom_serial: null`；
- `1.6RENAME`：1.6 修改 atom name；
- `1.6REPLACE`：1.6 whole-residue / coordinate replacement 中，输入输出可明确对应为同一 atom；
- `1.7RENAME`：1.7 修改该 atom 所属 residue 的 residue name；
- `1.8REORDER`：1.8 residue / component organization 实际改变该 atom 的输出位置；
- `2.2ADD`：pdb2gmx 新增 atom；输入 Stage 1 结构中无对应 atom；
- `2.5ADD`：2.5 按实际采用 topology definition 为直接采用定义的 solvent / ion residue 补入此前不存在的 atom。

同一 atom 在同一步实际经历多个已定义操作时，按实际发生顺序追加多个 code。

后续 Skill 如新增需要进入累积 atom provenance 的操作，先在本共享规则中定义新的 Step-specific code，再由对应 Skill 使用。

## 5. 1.3 初始化

1.3 不存在 input map。

对每个 1.3 local target：

- 先按 `target_lineage_rules.md` 建立当前 `targets/target_xxx.yaml`；其 `source_target_records: []`；
- map `target_record` 指向当前 1.3 target record；
- 以 1.2 实际检查结构作为 `original_structure` 与 `input_structure`；
- `input_map: null`；
- 对实际写入当前 target PDB 的每个 source atom 建立 record；
- `original_atom_serial` 取原始结构 serial；
- `current_atom_serial` 取 1.3 输出 PDB serial；
- `component_id + residue_id` 使用 1.2 正式 residue identity；
- `operations` 初始化为 `[1.3ADD]`；
- 未进入当前 target 的 atom 不写入该 map；
- selected missing residue 尚无 coordinates，不产生 atom record，待后续真正新增 atom 时建立。

1.3 当前 target PDB、current target record 与 atom map 必须相互对应。

## 6. 1.4 维护

1.4 为每个 current local target 建立自己的 target record，并用其 `source_target_records` 指向实际来源的 1.3 / 上游 target record。

输出 map：

- `target_record` 使用当前 1.4 target record；
- unselected-conformer atom record 删除；
- shared atom 保留原 history；
- surviving selected-conformer atom 保留 `original_atom_serial`、`component_id + residue_id`，按输出 PDB 更新 `current_atom_serial`；
- 对实际清除 surviving altLoc 的 atom 追加 `1.4ALTLOC`；
- serial 重编号本身不追加 operation。

同一个 source target 形成多个 1.4 targets 时，各输出 map 分别指向各自 current target record；它们的 target records 可以共同引用同一个 source target record，从而明确表示分支。

## 7. 1.6 维护

1.6 使用与 `structure_completeness_report.yaml.structure` 对应的最近正式 atom map 作为 `input_map`，同时为当前 1.6 local target 建立 current target record。

输出 map `target_record` 指向当前 1.6 target record；逐原子更新：

- confirmed extra atom 删除 → 删除对应 record；
- atom-name correction → 保留原 provenance，追加 `1.6RENAME`；
- missing heavy atom 新增 → 新 record，`original_atom_serial: null`，写 `1.6ADD`；
- missing residue 新增 → 全部新增 atoms 建新 record，写 `1.6ADD`；
- whole-residue / coordinate replacement：
  - 输入输出可明确对应同一 atom → 保留原 record 与 `original_atom_serial`，追加 `1.6REPLACE`；
  - 输出 atom 在输入结构确实不存在 → 新 record，`original_atom_serial: null`，追加 `1.6ADD`；
  - 输入 atom 无对应输出 → 从 output map 删除；
- 未修改 surviving atoms 只更新 serial。

不得因为 replacement 使用 reference coordinates，就把仍可明确对应输入 atom 的所有原子统一改成 `original_atom_serial: null`。

## 8. 1.7 维护

1.7 为当前 local target 建立 current target record，并复制与输入 heavy-atom structure 对应的正式 map。

输出 map：

- `target_record` 指向当前 1.7 target record；
- atom records 全部保留；
- `original_atom_serial`、`component_id + residue_id` 保持不变；
- `current_atom_serial` 与输出结构一致；
- residue name 实际变化的 residue，其全部 atoms 追加 `1.7RENAME`；
- 未变化 residue 不追加 operation。

## 9. 1.8 与 `stage1_final_map.yaml`

1.8 为当前 local target 建立 current target record，并复制与输入 heavy-atom structure 对应的正式 map。

`stage1_final_map.yaml`：

- `target_record` 指向当前 1.8 target record；
- 不新增或删除 atom record；
- 保持 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`；
- 按 `stage1_final.pdb` 更新 `current_atom_serial`；
- 对因 1.8 organization 实际改变输出位置的 atoms 追加 `1.8REORDER`。

最终正式 map basename：

```text
stage1_final_map.yaml
```

不另建第二套 final-map schema。

## 10. 2.2 维护

2.2 处理标准残基时，为当前 2.2 local target 建立 target record；其 `source_target_records` 指向实际作为当前标准残基处理对象来源的上游 target record。

以对应 `stage1_final_map.yaml` 为上游 map source，并按当前标准残基处理范围维护：

- `standard.map.target_record` 指向当前 2.2 target record；
- 不属于当前处理范围的 atom records 不进入 `standard.map`；
- 对应 Stage 1 atom 保留 `original_atom_serial`、`component_id + residue_id` 与既有 `operations`，按 `standard.gro` 更新当前 index；
- pdb2gmx 新增 atom 建新 record，`original_atom_serial: null`，保留所属 residue identity，写 `2.2ADD`；
- `input_structure` 指向实际 pdb2gmx 输入 PDB；
- `input_map` 指向实际使用的 `stage1_final_map.yaml`；
- `current_structure` 指向 `standard.gro`；
- basename 固定为 `standard.map`。

本环节不建立第二套 atom identity，也不根据输出 atom name、resid、chain 或 order 重建 `component_id + residue_id`。

## 11. Map validation

每个生成 map 的步骤至少确认：

- `target_record` 能定位当前 Step 当前 local target 的正式 target record；
- 当前 formal result 如记录 `references.target_record`，与 map `target_record` 一致；
- target record 的 `source_target_records` 与当前 Skill / Task Sheet 的实际 target 来源一致；
- 当前输出结构每个 atom 恰有一个 map record；
- map 不存在当前结构中没有的额外 atom record；
- `current_atom_serial` 在当前结构中唯一且可定位；
- `component_id + residue_id` 能定位当前 model 的 1.2 正式 residue；
- `original_atom_serial != null` 时，该 serial 能定位 `original_structure` 中唯一 atom；
- `original_atom_serial == null` 时，history 中存在使该 atom 进入结构的后续 `ADD` operation；
- copy-and-update 没有丢失或重写既有 operation history；
- 当前步骤新增 operation 与实际结构修改一致；
- `1.6REPLACE` 只用于输入 / 输出 atom correspondence 已明确的 replacement atom，不用于真正新增 atom。

1.9 对 `stage1_final.pdb` 与 `stage1_final_map.yaml` 重复执行最终一致性检查，但不修改 map。