# Skill 1.6 deterministic helpers

本目录只提供 1.6 可选的确定性结构处理能力。科学判断由 `../SKILL.md` 与 `../references/` 拥有；脚本不决定 repair scope、reference 选择、residue mapping、anchor expansion 或最终 PASS/FAIL。

当前两个 helper：

```text
transplant_coordinates.py
→ 根据 Agent 已确定的 correspondence / alignment atoms 计算 rigid transform
→ 输出 transformed coordinates 与机械 fit evidence

apply_structure_edits.py
→ 根据 Agent 已确定的 remove / rename / add / replace operations
→ 写出最终 PDB 并连续重编号 atom serial
```

这里直接定义脚本使用的数据格式；当前不另建 rigid schema。配置可以是 task-local 临时 YAML；`transplant_coordinates.py` 的结果默认写 stdout，也可以按需保存为 task-local YAML。Skill 不要求固定中间文件名或项目级登记。

## Dependencies

```text
Python 3
PyYAML
gemmi
numpy
```

## 1. transplant_coordinates.py

### CLI

```bash
python scripts/transplant_coordinates.py \
  --config <transplant_config.yaml> \
  [--output <transplant_result.yaml>]
```

不提供 `--output` 时，YAML 写到 stdout。`--output` 只在 Agent 需要把结果作为当前任务的临时机器输入保存时使用。

### Input format

```yaml
target_structure: /absolute/path/to/current_target.pdb
reference_structure: /absolute/path/to/reference.cif

target_model_index: 1       # optional; default 1
reference_model_index: 1    # optional; default 1

alignment_atoms:
  - target:
      chain_id: A
      resid: 96
      insertion_code: ""     # optional; default empty
      residue_name: GLY       # optional identity check
      atom_name: CA
      altloc: ""              # optional; default unique/current atom
    reference:
      chain_id: B
      resid: 100
      insertion_code: ""
      residue_name: GLY
      atom_name: CA
      altloc: ""

transplant_atoms:            # optional
  - target:
      chain_id: A
      resid: 125
      insertion_code: ""
      residue_name: ARG
      atom_name: NH2
    reference:
      chain_id: B
      resid: 127
      insertion_code: ""
      residue_name: ARG
      atom_name: NH2

transplant_residues:         # optional
  - target:
      chain_id: A
      resid: 101
      insertion_code: ""
      residue_name: GLY
      record_name: ATOM      # optional; default ATOM
    reference:
      chain_id: B
      resid: 105
      insertion_code: ""
      residue_name: GLY
```

Requirements:

- `alignment_atoms` 至少 3 对，且 reference 侧坐标与 target 侧坐标都不能共线；
- 每个 atom / residue selector 必须在对应 model 中唯一定位；若存在无法消除的 altLoc 歧义，脚本失败而不是猜测；
- `target` identity 是最终写入身份，`reference` identity 只用于坐标读取；
- `transplant_residues` 输出 reference residue 的重原子，不输出 H；
- `transplant_atoms` 只输出显式列出的 atom；
- 允许同时包含 `transplant_atoms` 与 `transplant_residues`，但同一 target atom 不得重复出现。

完整 polymer-chain residue mapping、anchor 选择等科学工作信息由 Agent 按 `../references/missing_residue_completion.md` 维护；只有本次真正用于 rigid alignment / transplant 的对应关系需要传给脚本。

### Output format

```yaml
target_structure: /absolute/path/to/current_target.pdb
reference_structure: /absolute/path/to/reference.cif

alignment:
  atom_count: 8
  rmsd: 0.42
  rotation:
    - [r11, r12, r13]
    - [r21, r22, r23]
    - [r31, r32, r33]
  translation: [tx, ty, tz]

transplanted_atoms:
  - target:
      chain_id: A
      resid: 101
      insertion_code: ""
      residue_name: GLY
      atom_name: N
      record_name: ATOM
      element: N
    reference:
      chain_id: B
      resid: 105
      insertion_code: ""
      residue_name: GLY
      atom_name: N
    coordinates:
      x: 1.234
      y: 2.345
      z: 3.456
```

输出只表示确定性几何结果。它不包含 `PASS`、`acceptable`、`best_reference`、`should_use` 等科学 verdict。

## 2. apply_structure_edits.py

### CLI

```bash
python scripts/apply_structure_edits.py \
  --config <structure_edit_config.yaml>
```

本脚本只处理单-model PDB target，并写出新的 PDB；不覆盖输入文件。

### Input format

```yaml
input_structure: /absolute/path/to/current_target.pdb
output_structure: /absolute/path/to/completed_structure.pdb

remove_atoms:
  - chain_id: A
    resid: 25
    insertion_code: ""
    residue_name: LEU
    atom_name: XX
    altloc: ""

rename_atoms:
  - target:
      chain_id: A
      resid: 30
      insertion_code: ""
      residue_name: DA
      atom_name: O1P
      altloc: ""
    new_atom_name: OP1

add_atoms:
  - target:
      chain_id: A
      resid: 125
      insertion_code: ""
      residue_name: ARG
      atom_name: NH2
      record_name: ATOM
      element: N
    coordinates: {x: 1.234, y: 2.345, z: 3.456}

add_residues:
  - target:
      chain_id: A
      resid: 101
      insertion_code: ""
      residue_name: GLY
      record_name: ATOM
    atoms:
      - atom_name: N
        element: N
        coordinates: {x: 1.0, y: 2.0, z: 3.0}
      - atom_name: CA
        element: C
        coordinates: {x: 1.5, y: 2.5, z: 3.5}

replace_residues:
  - target:
      chain_id: A
      resid: 125
      insertion_code: ""
      residue_name: ARG
      record_name: ATOM
    atoms:
      - atom_name: N
        element: N
        coordinates: {x: 1.0, y: 2.0, z: 3.0}
```

`replace_residues` 用于已经明确按完整 residue completion 处理的 partial residue：脚本先移除该 target residue 的现有 coordinate records，再写入给定完整重原子集合。是否需要 replace 由 Agent 根据 Skill/reference 判断，脚本不自行转换 repair type。

### Consuming transplant output

`transplant_coordinates.py` 的 `transplanted_atoms` 可以由 Agent 直接转成 `add_atoms`，或按 target residue 分组后转成 `add_residues` / `replace_residues`。这一步是当前任务的工作数据整理，不要求产生固定命名中间文件。

如果 Agent 选择保存 `transplant_coordinates.py --output` 的 YAML，只把它作为 task-local working material；`apply_structure_edits.py` 不依赖任何固定文件名。

### Writer rules

`apply_structure_edits.py`：

- selector 必须唯一命中需要 edit 的现有 PDB atom / residue；
- 不从 reference structure 推断 target identity；
- 不自行决定删除、rename、补 atom 或 replace residue；
- 不添加 config 未提供的 atom；
- 不接受 H 作为新增 atom；
- 保持未被 edit 的 atom/residue identity 与相对顺序；PDB 文本由 gemmi 重新序列化，不承诺逐行保留输入文件格式；
- 新增 atom 插入对应 residue，新增 residue 插入同 chain 的 residue 顺序位置；
- 最终 ATOM/HETATM serial 从 1 开始连续、唯一重编号；
- 输入含 `CONECT` record 时拒绝写入，因为 serial renumbering 需要显式 connectivity handling；
- `CRYST1` 只在输入本身存在时写出；
- `output_structure` 已存在时默认失败，不静默覆盖。

## Exit codes

```text
0  deterministic operation completed
2  input/config/identity/geometry consistency failure
3  unexpected internal failure
```

这些 helper 的成功退出只说明确定性操作成功；1.6 科学 validation 仍按 `../SKILL.md` 执行。
