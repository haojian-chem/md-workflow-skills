# Workflow 1 / Stage 1.6 Structure completion architecture freeze

Status: **FROZEN AUTHORING REFERENCE — NOT AN ACTIVE SKILL**

## 0. 文档定位

本文件保存 `1.6 Structure completion / correction` 已经讨论并敲定的设计事实，以及后续正式生成 Skill 时需要直接继承的细节。

它不是 `SKILL.md`，也不表示 1.6 已经获得正式 Skill generation / activation 许可。正式 Skill 生成时，应以本 freeze + 当时 current 的 1.5/相邻 Skill + authoring rules 为输入，不重新从零讨论已经冻结的内容。

本文件迁移并保留了此前误放入 active Skill 路径的 1.6 详细内容，同时合并保留历史 Operation / Validator 中的有效信息；不恢复旧 Workflow / Operation / Validator 角色分类。

Source preservation:

- former active pseudo-Skill: `01_structure_preparation/1.6_missing_region_completion/SKILL.md`, blob `5108970ba61c2c913e57039a54238e6b8bf150a8`
- historical operation source: `02_operations/missing_region_completion/SKILL.md`, blob `4dbafe0f7501ebd5e36e4d45486b52809f3a248e`
- historical validation source: `02_validators/missing_region_completion_validator/SKILL.md`, blob `73c7982650c3e9862213c67981bc59c684376b7b`

## 1. Purpose and boundary

1.6 的目标是把 1.5 已经明确的 Stage 1 repair items 落实到当前保留结构，使后续质子化状态判断和最终结构整理消费一个 composition-correct 的重原子结构。

1.6 只执行 1.5 已明确的问题，不重新判断什么是 missing / extra / mismatch，不扩大 repair scope。

1.6 不负责：

- 重新执行 1.5 completeness/problem determination；
- force-field-specific terminal conversion；
- 标准残基最终加氢；
- Stage 2 的 all-atom / topology processing。

## 2. Required object / evidence

生成正式 1.6 Skill 时，至少应消费：

- 当前保留 target 的现行 PDB；
- 1.5 正式 `structure_completeness_report.yaml`；
- 补全缺失残基或重原子所需的参考结构 / 模板；
- 上游已经确定的 residue / atom identity 与 rename 对应关系。

1.6 只处理 1.5 report 中属于当前 target 且明确交给 1.6 的 repair items。

## 3. Frozen repair sequence

处理顺序冻结为：

```text
删除 confirmed extra atoms
→ 校正 confirmed atom-name mismatches
→ 补全 missing residues
→ 补全 missing heavy atoms
→ 按最终写入顺序重新连续编号 atom serial
```

顺序含义：

1. `extra atom`：按 1.5 已确认结论删除；
2. `atom-name mismatch`：按已确认对应关系改名，保留原坐标和原子身份；
3. `missing residue`：插入 chain 中正确 residue 位置；
4. `missing heavy atom`：在对应 residue 中补入；
5. 统一连续重编号。

除 report 明确要求的修改以及补全所必需的局部处理外，不自行扩展修复范围。

## 4. Missing heavy atom completion

缺失重原子处理冻结为：

- 优先使用 AF3 完整残基模板或 CCD 完整残基模板；
- 使用当前残基中已有共同重原子进行模板对齐；
- 只移植缺失重原子；
- 不为了补一个缺失重原子而替换当前 residue 中已有且有效的重原子坐标；
- 不在 1.6 添加最终 H。

## 5. Missing residue completion

缺失残基处理冻结为：

- 使用 AF3 生成的对应完整结构或用户提供的 AF3 结构作为主要参考；
- 先建立 chain / sequence residue correspondence；
- 使用缺失区两侧现有残基做局部双侧对齐；
- anchor region 采用逐步向两侧扩展策略，而不是预先固定 N 个残基；
- 优先采用能够给出稳定、几何一致局部叠合的最小双侧 anchor 区域；
- 只移植缺失 residue；
- 如果缺失区两侧不能同时得到合理局部叠合，不强行插入；应改用其他参考/model，或在确有科学歧义时向用户确认。

完成后的 missing residues 必须回到 polymer chain 的正确 residue 位置，供后续 1.8 organization/mapping 使用。

## 6. Reuse model to carry into Skill generation

已有 1.6 结果只有在以下条件均明确等价时才可自动复用：

- 输入结构相同；
- 1.5 repair report 相同；
- 实际使用的补全参考 / 模板相同；
- 所有影响结果的人工决定相同。

明确变化时重新执行；信息不足时由后续正式 Skill 按 Lightweight Runtime 的通用原则处理。

## 7. Validation boundary

Validation 属于 1.6 结果 owner，不需要恢复独立 Validator layer。

逐项核验 1.5 repair report：

- missing residue → 对应 residue 已补入正确 chain / residue 位置；
- missing heavy atom → 对应 heavy atom 已存在；
- extra atom → 已删除；
- atom-name mismatch → 已按确认关系改名。

同时检查：

- `completion_report.yaml` 与实际 PDB 修改一致；
- 没有超出 1.5 report 的未记录删除 / 改名；
- 输出不存在重复 atom identity；
- atom serial 连续且唯一；
- PDB 可正常解析；
- 新增 residue / heavy atom 的局部连接与几何没有明显不合理；
- 没有添加本应留给后续步骤处理的最终 H；
- `unresolved_items` 为空。

任一应处理项目未解决时，1.6 不能视作完成。Validation 不重新做 1.5 的问题判定，也不自行扩展 repair scope。

## 8. Frozen results / handoff

后续正式 Skill 的结果方向至少包括：

```text
completed_structure.pdb
completion_report.yaml
completion_validation.md
```

`completion_report.yaml` 至少记录：

- added residues；
- added heavy atoms；
- removed atoms；
- renamed atoms；
- unresolved items（若存在）。

既有 execution-directory 约定为：

```text
01_structure_preparation/06_missing_region_completion/<task_id>/
```

该路径是科研项目 execution directory，不是本仓库 Skill source directory。

## 9. Handoff to 1.7

如果 1.6 实际修改了结构，1.7 必须消费 1.6 当前正式结构，而不是回退到旧输入。

1.6 输出仍是重原子结构；蛋白质 protonation-state assignment / residue naming 由 1.7 负责，标准残基最终 H 继续留给 Stage 2。

## 10. Skill-generation note

正式生成 1.6 Skill 时：

- 直接继承本 freeze 中已敲定的科学与 validation 边界；
- 不恢复旧 `Operation + Validator` 双层包装；
- 不因为模板需要而重新讨论已经冻结的 repair sequence / AF3-CCD completion / bilateral alignment 规则；
- 只有实现层文件名、reference 拆分、确定性 Tool 等尚未冻结的内容，才在 authoring 阶段继续细化。
