---
name: chain_and_component_selection_validator
description: 核验 chain_and_component_selection 生成的候选结构、selection manifest 和源到输出 mapping，确认选择集合、模型、原子完整性、身份映射、坐标属性及显式连接符合已解决 selection spec。该 Validator 不修改候选结构，也不重新解释用户选择。
---

# 目标

验证 1.3 Operation 是否准确执行显式 selection spec：

- 输出只包含选中 model/component/residue/atom；
- 没有漏掉选中 residue 的 atom 或 altLoc；
- 没有额外保留未选对象；
- identity、坐标、occupancy 和 B factor 保持；
- confirmed covalent relations 没有被切断；
- manifest 和 mapping 与源/输出事实一致；
- 输出可作为后续 altLoc/completeness 检查的 STRUCTURE candidate。

# 职责边界

负责：

- 读取源 STRUCTURE、classification result、selection spec；
- 读取 Operation candidate、manifest、mapping 和 report；
- 重新解析源与候选结构；
- 独立计算 expected selected set；
- 比较实际 residue/atom 集合；
- 核验一对一 mapping 与坐标属性；
- 核验 confirmed covalent closure 和输出连接；
- 核验 hashes、provenance 和 output format；
- 返回 Validation result、artifact candidate gate 和详细 report。

不负责：

- 修改或修复候选结构；
- 扩展或缩小用户选择；
- 重新决定 model/component；
- 处理 altLoc/occupancy 冲突；
- 判断缺失残基或重原子；
- 分配质子化状态；
- 将 metal coordination 解释为共价连接；
- 写管理目录；
- 自动重试 Operation。

# 输入

作为 `OPERATION_WITH_VALIDATOR` task unit 的 validator 部分，必须接收：

- 同一 task 的 Operation result；
- 源 STRUCTURE file record；
- classification result；
- selection spec；
- candidate selected structure；
- selection manifest；
- selection mapping；
- Operation report；
- allowed read/write 和 forbidden paths；
- 本 Validator report/result data 路径。

Operation 未产生完整候选文件时返回 `BLOCKED` 或 `FAILED`，不得推测缺失内容。

# Preflight

确认：

- task mode 为 `OPERATION_WITH_VALIDATOR`；
- operation/validator refs 正确；
- Operation result 与 task/workstream IDs 一致；
- Operation status 为 DONE；
- required candidate files 存在、可读、非 symlink；
- source/classification/spec hashes 与 manifest 一致；
- Validator 输出路径位于 allowed write paths；
- 源和候选结构均不是 Validator 写入目标；
- 管理目录位于 forbidden paths。

# 独立期望集合

Validator 不直接信任 manifest 中的 selected residue/atom lists。

必须从：

```text
classification result + selection spec
```

重新计算：

- selected model；
- selected components；
- expected residue IDs；
- expected atom identities；
- expected explicit relations；
- excluded components/residues；
- coordination/candidate relations that cross the boundary。

若 spec 本身切断 confirmed covalent relation，Validator 返回：

```text
INVALID_SELECTION_SPEC_COVALENT_BREAK
```

不得通过候选结构已删除连接而掩盖 spec 错误。

# 核验内容

## 结构集合

候选结构必须：

- 仅包含 selected model；
- residue set 与 expected set 完全相同；
- 每个 selected residue 的 atom identity multiset 与源结构相同；
- 不包含 excluded residue 或 atom；
- 不遗漏 altLoc。

## 身份与映射

`selection_mapping.yaml` 必须：

- 每个输出 atom 恰有一个源 atom；
- 每个 expected source atom 恰映射到一个输出 atom；
- 不存在多对一或一对多；
- 映射使用 model/chain/residue/insertion/atom/altLoc 等稳定字段；
- atom serial 变化不影响身份核验，但必须记录；
- 输出 identifiers 的任何变化必须符合明确 format constraint，v1 默认不允许隐式改名或改号。

## 坐标属性

源与输出对应 atom 应保持：

- x/y/z；
- occupancy；
- B factor；
- element；
- formal charge，如格式可表达。

坐标默认绝对容差：

```text
1e-4 Å
```

PDB 格式舍入可使用 schema/rules 明确的格式容差，但不得掩盖真实移动。

## 连接

- 两端均被选中的 confirmed covalent connection 必须保留或可由输出事实无歧义恢复；
- 不得保留指向已删除 atom 的显式连接；
- disulfide/glycosidic/covalent relation 不得被静默删除；
- metal coordination 可被选择边界切分，但必须在 manifest/report 中准确记录；
- geometry-only candidates 不作为强制连接 gate。

## Manifest

核验：

- source/classification/spec/output hashes；
- selected model/component IDs；
- requested vs actual selection；
- selected/excluded residue 与 atom counts；
- preserved/removed/cross-boundary relation lists；
- output format/path；
- policies 固定值；
- decision provenance。

## 源文件保护

源 STRUCTURE、classification result 和 selection spec 的 SHA-256 必须与执行前一致。

# Gate outcomes

- `SELECTION_VALIDATED`：所有 required checks 通过；
- `SELECTION_VALIDATED_WITH_WARNINGS`：仅存在不影响选择正确性的格式/metadata warning；
- `INVALID_SELECTION_SPEC_COVALENT_BREAK`；
- `SELECTED_SET_MISMATCH`；
- `ATOM_MAPPING_MISMATCH`；
- `COORDINATE_OR_ATTRIBUTE_CHANGED`；
- `EXPLICIT_CONNECTION_MISMATCH`；
- `MANIFEST_OR_HASH_MISMATCH`；
- `OUTPUT_FORMAT_MISMATCH`；
- `VALIDATOR_INPUT_INCOMPLETE`；
- `SELECTION_VALIDATOR_INTERNAL_FAILURE`。

# 通过条件

只有：

```text
SELECTION_VALIDATED | SELECTION_VALIDATED_WITH_WARNINGS
```

可以建议 Manager 接受 Operation 的 STRUCTURE artifact candidate。

通过仅表示：

- 选择被准确执行；
- mapping 和结构身份一致；
- 没有非预期结构修改。

不表示：

- altLoc 已解决；
- 结构完整；
- 质子化正确；
- 已满足 topology_preparation 最终 gate。

# 输出

默认：

```text
01_structure_preparation/03_chain_and_component_selection/
├── chain_and_component_selection_validation_report.yaml
└── selection_validation_result.yaml
```

返回共享 `subagent_result` v2 中独立的 `validation_result`：

- `status` 与实际执行一致；
- `outcome_code` 使用上述值；
- `validated_files` 包含候选结构、manifest 和 mapping；
- `created_files` 包含 Validator report/result data；
- warnings/failure 结构化；
- 不修改 Operation component result；
- 通过时允许 top-level STRUCTURE artifact candidate；
- 失败时不得将候选标为有效或 VALIDATED。

# 失败处理

- 输入不完整：BLOCKED；
- 候选不可解析或核验失败：FAILED；
- 不自动修复或重跑 Operation；
- 保留详细差异 report；
- 不覆盖其他 task 输出；
- 不写管理目录。

# 自检

- [ ] expected set 由 classification + spec 独立重算；
- [ ] 未信任 manifest 自报结果；
- [ ] residue/atom/altLoc 集合完全一致；
- [ ] mapping 一对一且完整；
- [ ] 坐标和属性在容差内不变；
- [ ] confirmed covalent connections 未被切断；
- [ ] coordination 未被误用为共价 gate；
- [ ] manifest/hash/provenance 一致；
- [ ] 源文件未改变；
- [ ] 未修改候选结构；
- [ ] 通过范围没有被表述为最终结构质量通过；
- [ ] 未写管理目录。
