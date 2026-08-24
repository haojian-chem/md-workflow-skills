# PDB materialization rules

# 1. 输出

每个 target 固定生成一个 PDB：

```text
structures/target_xxx.pdb
```

只输出：

- `CRYST1`（当前结构存在有效晶胞信息时）；
- `ATOM`；
- `HETATM`；
- `TER`；
- `END`。

不输出 `LINK`、`SSBOND`、`CONECT`。

# 2. Chain label

1.3 为当前 1.2 model 的每个 `component_id` 建立自己的 `chain_index`。`chain_index` 按 1.2 `components[]` 的正式数组顺序从 1 编号，因此同一个 `component_id` 在不同 target 中保持同一个 1.3 `chain_index`。

PDB chain ID 再由该 1.3 `chain_index` 固定映射：

```text
A-Z → a-z → 0-9
```

例如：

```text
chain_index 1  → A
chain_index 2  → B
chain_index 27 → a
```

不同 target 使用同一映射。不得因为某个 target 没有选择部分 component 而重新压缩 chain ID。

这里的 `chain_index` 是 1.3 输出 mapping 的局部编号，不属于 1.2 identity，也不得写回 1.2 `classification_result.yaml`。

如果当前所需字段无法按本步骤固定 PDB 表示可靠写出，停止生成并向用户说明具体问题后确认处理方式。

# 3. Residue order 与 resid

selected residue 的先后顺序使用 1.2 正式层级中的顺序：

```text
components[] 顺序
→ 每个 component 内 residues[] 顺序
```

不按 `residue_id`、`component_id` 或 source resid 数值重新排序。

每个 1.3 `chain_index` 独立分配 resid，并从 1 开始。

所有 selected residues 都占一个 resid，包括 1.2 中 `missing_residue_check.status: ISSUE` 的 residue：

- selected missing residue 不生成坐标记录，因此可以形成 resid 跳号；
- 未被 selected 的 residue 不占 resid；
- 同一 `chain_index` 中经过 `TER` 后 resid 不重新从 1 开始。

# 4. ATOM / HETATM

直接使用 1.2 residue 的 `polymer_class.value`：

```text
POLYMER    → ATOM
BRANCHED   → HETATM
NONPOLYMER → HETATM
WATER      → HETATM
```

# 5. TER

对于 `POLYMER`：

- 连续 selected polymer block 内不在每个 residue 后写 `TER`；
- 每个 selected polymer block 结束时写一个 `TER`；
- selected missing residue 不切断 polymer block；
- 未 selected residue 造成的区段断开形成新的 polymer block。

对于 `BRANCHED`、`NONPOLYMER`、`WATER`，每个实际输出 residue 后写一个 `TER`。

`TER` 不改变 PDB chain ID，也不重置 resid。

# 6. Atom records

只为当前具有坐标的 selected residues 写入 atom records。

同一个 residue 内保留当前结构中的 atom record 顺序。

保留当前结构中的：

- atom name；
- altLoc；
- residue name；
- coordinates；
- occupancy；
- B-factor；
- element；
- formal charge。

重新生成的表示字段包括：

- `ATOM` / `HETATM` record type；
- PDB chain ID；
- resid；
- atom serial；
- `TER`。

atom serial 按实际写入 PDB 的 `ATOM` / `HETATM` / `TER` 顺序从 1 连续编号，不为 missing residue 预留编号。

# 7. Target mapping

PDB 生成后，在对应 `targets/target_xxx.yaml` 中补充：

- `chain_mapping`；
- `residue_mapping`。

`chain_mapping` 记录：

```text
1.3 chain_index ↔ component_id ↔ pdb_chain_id
```

`residue_mapping` 使用：

```text
chain_index + resid ↔ component_id + residue_id
```

所有 selected residues 都必须有 mapping，包括没有坐标的 selected missing residues。
