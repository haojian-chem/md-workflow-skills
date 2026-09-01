# 1.3 validation

验证 1.3 生成的 target 记录和 PDB 是否忠实于用户确认的 selection，并符合本步骤的 PDB materialization 规则。Validation 只读取和检查当前结果，不修改被验证对象。

## Object requirements

验证需要：

- 用户已确认的 1.3 selection；
- 1.2 正式 `classification_result.yaml`；
- 与 1.2 对应的当前结构；
- `selection_index.yaml`；
- `targets/target_*.yaml`；
- `structures/target_*.pdb`。

## Checks

### Selection

检查：

- `selection_index.yaml` 中的 target 与用户确认的 target 数量和含义一致；
- `target_xxx.yaml` 中的 `component_id + residue_ids` 与用户要求一致；
- 每个 `residue_id` 属于记录的 `component_id`；
- selected missing residues 已包含在 selection 中。

### Structure content

检查：

- 当前有坐标的 selected residues 均出现在 PDB 中；
- selected missing residues 没有被凭空生成坐标；
- PDB 中没有混入未 selected residue；
- 每个实际输出 residue 的 atom set 与当前结构一致；
- residue 内 atom record 顺序保持不变；
- atom name、altLoc、residue name、coordinates、occupancy、B-factor、element、formal charge 未发生非预期改变。

### PDB organization

按照 `references/pdb_materialization_rules.md` 检查：

- chain ID；
- resid；
- `ATOM` / `HETATM`；
- `TER`；
- atom serial；
- PDB record 组织。

### Mapping

检查：

- `chain_mapping` 与实际 PDB chain ID 一致；
- `residue_mapping` 对所有 selected residues 完整且无重复；
- 每条 `chain_index + resid` 都正确对应 1.2 `component_id + residue_id`；
- selected missing residues 虽无坐标，仍保留正确 residue mapping。

## Result

在当前 Task Sheet 的 1.3 工作目录写入 `selection_validation.md`。存在多个 target 时逐个记录检查结果。

任一检查项为 `FAIL` 时，当前 1.3 保持未完成；修正后重新验证。
