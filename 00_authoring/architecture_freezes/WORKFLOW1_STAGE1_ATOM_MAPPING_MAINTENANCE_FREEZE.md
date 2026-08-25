# Workflow 1 / Stage 1 atom mapping maintenance architecture freeze

Status: **FROZEN AUTHORING RECORD — RUNTIME RULE MATERIALIZED**

Current shared runtime authority:

```text
references/atom_mapping_rules.md
```

本文件只保存 Stage 1 内部原子映射维护的架构边界。执行规则由 `references/atom_mapping_rules.md` 拥有；相关 active Skill 必须显式引用该 runtime reference。

## 1. Baseline

Stage 1 后续原子映射以 1.2 所检查的原始结构、1.2 `classification_result.yaml` 中的 `component_id + residue_id` 以及当前 target 的 chained atom map 共同维持。

1.2 本身不承担 atom mapping，因此不引用该共享 runtime reference。

## 2. Applicable steps

当前 chained map 由以下步骤维护：

```text
1.3  初始化 target atom map
1.4  copy + update
1.6  copy + update
1.7  copy + update
1.8  copy + update → stage1_final_map.yaml
```

1.5 不修改结构，不维护 map。

1.9 读取 shared runtime reference，用于 Stage 1 final PDB / final map 的逐原子与 provenance 验证。

## 3. Fixed map identity fields

每个当前 atom record 固定保留：

```text
current_atom_serial
original_atom_serial
component_id
residue_id
operations
```

其中：

- `current_atom_serial` 随当前输出结构更新；
- `original_atom_serial` 指向 1.2 所检查原始结构中的 atom serial，后续新增 atom 为 `null`；
- `component_id + residue_id` 保持项目内部 residue identity；
- `operations` 累积保留 Step-specific operation history，例如 `1.3ADD`、`1.6ADD`。

不建立永久 `atom_id`。

## 4. Copy-and-update architecture

1.3 为每个 target 初始化 map；1.4、1.6、1.7、1.8 都必须复制与当前输入结构对应的正式 map，再基于本步骤实际结构操作维护副本。

输出 map 只包含当前输出结构中实际存在的 atoms：

- 删除 atom → 删除对应 row；
- surviving atom → 保留 `original_atom_serial`、`component_id + residue_id` 与既有 operation history，并更新 `current_atom_serial`；
- rename / altLoc cleanup / residue-name modification / reorder → 在 surviving atom 的 `operations` 末尾追加对应 Step-specific code；
- 新增 atom → 新建 row，`original_atom_serial: null`，并记录当前 Step 的 `ADD` operation。

历史 operation 不得由后续步骤删除或改写。

具体字段结构、operation code 与逐步骤更新规则由 current `references/atom_mapping_rules.md` 拥有，不在本 freeze 维护第二套可变规范。

## 5. Boundary

本 freeze 只授权并规定 Stage 1 原子映射维护。Stage 2 的 atom mapping / provenance 语义不在本文件中定义，也不由本次 authoring 变更决定。
