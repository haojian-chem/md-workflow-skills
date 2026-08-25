# Stage 1 原子映射维护共享规则

本文件是 Stage 1 中结构改写步骤共同使用的 atom-mapping runtime reference。凡步骤会改变当前结构的 atom set、atom name、residue name、atom order、altLoc 表示或 atom serial，都必须读取本文件并保持输入结构到输出结构的原子对应关系可追溯。

当前适用步骤：

```text
1.3 Chain and residue selection
1.4 Alternate conformation / occupancy resolution
1.6 Structure completion
1.7 Protein protonation assignment
1.8 Reorder and mapping
```

1.5 不修改结构，因此不需要读取本文件。1.9 读取本文件用于验证 Stage 1 final atom map。

本文件只规定 Stage 1 的原子映射维护；不定义 Stage 2 的 mapping / provenance 语义。

## 1. 映射基准

Stage 1 后续原子映射以以下信息共同作为基准：

```text
1.1 / 1.2 对应的初始结构
+ 1.2 classification_result.yaml 中的 component_id + residue_id
+ 当前步骤的输入结构
+ 前序实际结构改写步骤的正式结果
```

其中：

- `component_id + residue_id` 用于保持 residue identity；
- 具体 atom 由当前结构中的实际 atom record 与 `atom_name` 定位；
- 在 1.4 处理前，如同名 atom 存在多个 alternate conformer，必要时还需结合实际 altLoc / 当前 atom record 区分；
- PDB atom serial 可以被后续步骤重新编号，因此不得把跨步骤不变的 serial 当作稳定 atom identity。

不要求 1.2 建立 atom-level identity，也不要求为 Stage 1 新增一套贯穿所有步骤的永久 `atom_id`。

## 2. 所有结构改写步骤的共同要求

任何适用步骤生成新的结构时，必须能够根据该步骤的正式输入、输出和正式结果判断每个受影响 atom 属于以下哪一种情况：

```text
SURVIVED   输入 atom 在输出结构中继续存在
REMOVED    输入 atom 被当前步骤删除
RENAMED    输入 atom 继续存在，但 atom name 或所属 residue name 被当前步骤修改
ADDED      输出 atom 是当前步骤新增，在输入结构中不存在对应 atom
```

不要求把这些词作为新的 YAML 枚举写入每个步骤的结果；它们只定义共享的映射语义。

共同规则：

- 未被当前步骤明确修改的 surviving atom，必须保持可与输入结构中的对应 atom 唯一关联；
- 删除、rename、新增或整 residue replacement 必须由该步骤现有正式结果记录到足以恢复输入 → 输出对应关系的程度；
- 单纯 atom serial 重编号不得被解释为 atom identity 改变；
- 单纯 atom / residue block reorder 不得破坏 atom correspondence；
- 不允许出现正式结果未记录、但会导致输入 → 输出 atom correspondence 无法解释的静默结构修改；
- 每个步骤继续使用自己已经确定的正式报告 / target record，不为共享原子映射额外复制一套平行结果文件。

## 3. 1.3 selection / PDB materialization

1.3 从当前 model 结构中保留用户选定的 research objects 并生成 target PDB，因此输出 atom set 通常是输入 atom set 的子集。

映射维护要求：

- `targets/target_xxx.yaml` 中的 `component_id + residue_id` / `residue_mapping` 是 target residue identity 的正式锚点；
- selected residue 中实际保留的 atom 均视为输入结构对应 atom 的 `SURVIVED`；
- 未被当前 target 选择的 atom 不进入该 target，视为该 target 分支中的 `REMOVED`；
- 1.3 若重新 materialize chain / resid / atom serial，这些表示变化不得被解释为新的 atom；
- 1.3 不修改 atom name、coordinates 或 alternate-conformation identity，除非其自身已有明确规则要求；不得为了生成 target PDB 静默改写原子身份。

1.3 不要求生成独立 atom-map 文件；当前 target PDB、target record、初始结构与 1.2 residue identity 共同保持后续可追溯性。

## 4. 1.4 alternate-conformation resolution

1.4 会删除未选构象 atom、清除 surviving selected atoms 的已解析 altLoc，并重新编号 serial。

映射维护要求：

- shared atoms 与 selected-conformer atoms 继续对应输入结构中的原 atom，视为 `SURVIVED`；
- unselected-conformer atoms 视为 `REMOVED`；
- 清除 selected atom 的 altLoc 只改变表示，不产生新 atom；
- `altloc_resolution_report.yaml` 必须使 selected conformer / affected object 足以与 source / generated PDB 对应，从而能够判断哪些 atom 被保留、哪些被删除；
- serial 重编号不改变 surviving atom correspondence。

## 5. 1.6 structure completion

1.6 可能删除 extra atom、修正 atom name、补入 missing heavy atom、补入 missing residue，或以 whole-residue completion 替换原 partial residue。

映射维护要求：

- `removed_atoms` 中的 atom 视为 `REMOVED`；
- `renamed_atoms` 必须保留 observed atom name → reference atom name，对应 atom 视为 `RENAMED`，其余身份连续；
- `added_heavy_atoms` 中新增 atom 视为 `ADDED`，不伪造其在输入结构中的对应 atom；
- `added_residues` 中实际新增的 residue / atom 视为 `ADDED`；
- whole-residue completion 若删除原 partial residue atom，再写入 replacement atoms：被删除的旧 atom 按 `REMOVED` 处理，replacement atoms 按 `ADDED` 处理；
- final atom-serial 重编号不改变 surviving / renamed atom 的 correspondence。

`completion_report.yaml` 必须与实际结构修改一致，并承担本步骤 atom-mapping continuity 所需的 change record；不另建平行 atom-change report。

## 6. 1.7 protein protonation assignment

1.7 当前只修改 residue name，不改变 heavy-atom set、atom name、coordinates 或 atom order。

因此输入与输出 atom 应逐 atom 一一对应：

```text
input atom
→ same component/residue identity
→ same atom_name / coordinates / order
→ residue_name 按 protonation assignment 更新
```

residue-name modification 视为映射中的 locator metadata 更新，不产生新 atom。`protonation_assignment_report.yaml` 中的 original / final residue name 与输出结构必须足以恢复该变化。

## 7. 1.8 reorder and final map

1.8 不新增或删除 atom，但会进行 object / residue block organization 并重新 materialize atom / TER serial。

映射维护要求：

- 进入 1.8 的每个实际 heavy atom 在输出 `stage1_final.pdb` 中恰有一个对应 atom；
- reorder 只改变写出位置，不改变 atom correspondence；
- final serial 是 `stage1_final.pdb` 的当前表示，不要求与任何上游 serial 相同；
- 1.8 使用当前结构、1.3 target residue mapping、1.2 `component_id + residue_id` 以及必要的前序正式 change record，生成最终 `stage1_final_map.yaml`。

`stage1_final_map.yaml` 中每个实际重原子保存：

```text
serial
chain_id
resid
residue_name
atom_name
component_id
residue_id
```

不因为前序存在删除、rename 或新增 atom 而伪造不存在的初始 atom identity。

## 8. 1.9 final atom-map validation

1.9 独立验证 `stage1_final.pdb` 与 `stage1_final_map.yaml` 的逐原子一一对应：

- final PDB 每个 `ATOM / HETATM` 原子在 map 中恰有一条记录；
- map 不包含 final PDB 中不存在的额外 atom record；
- 对应记录的 `serial + chain_id + resid + residue_name + atom_name` 与 final PDB 实际原子一致；
- 每条 map record 的 `component_id + residue_id` 能定位到当前 1.2 正式 residue。

1.9 不新增 atom identity，也不修改任何上游映射结果。
