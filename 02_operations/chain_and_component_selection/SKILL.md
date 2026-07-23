---
name: chain_and_component_selection
description: 根据已解决的用户决定、1.2 分类结果和结构化 selection spec，从一个已识别的 PDB/mmCIF/AF3 CIF 中选择一个模型及明确的链/组分集合，生成新的候选结构、选择清单和源到输出映射。该 Operation 不猜测用户要保留的对象，不处理 altLoc、缺失补全、质子化或重排编号，也不得切断已确认共价连接。
---

# 目标

为 `structure_preparation_workflow` 的 1.3 子步骤生成一个明确选择后的 STRUCTURE candidate：

- 从分类报告中引用稳定 component IDs；
- 选择一个 model；
- 保留 selection spec 明确列出的 component 集合；
- 排除未选择 component；
- 保留选中 component 的全部 residues、atoms、altLoc 和坐标属性；
- 生成 selection manifest、mapping 和 Operation report；
- 将候选结构交给专属 Validator，不自行声明通过。

# 职责边界

负责：

- 读取唯一授权源 STRUCTURE、classification result 和 selection spec；
- 核验 selection spec 与 task、源结构及分类结果的 ID/hash 关系；
- 根据 component IDs 计算精确保留集合；
- 检查选择是否切断已确认共价连接；
- 按明确 output format 生成候选结构；
- 写 manifest、mapping、Operation report 和必要日志；
- 返回 Operation component result 和 STRUCTURE artifact candidate。

不负责：

- 从自然语言猜测链或组分选择；
- 在缺少 selection spec 时默认保留全部或仅保留蛋白；
- 自动删除水、离子、辅因子、金属或配体；
- 因金属配位自动保留或排除 component；
- 切断 disulfide、peptide、glycosidic 或其他已确认共价连接；
- 选择 residue 子区间或切割聚合物链；
- 处理 altLoc/occupancy；
- 改变 atom name、residue name、chain ID、residue number、insertion code、坐标、occupancy 或 B factor；
- 补全缺失对象或分配质子化状态；
- 修改源结构；
- 写 `00_project_state/**` 或 `00_project_records/**`；
- 自行标记候选结构为 VALIDATED。

# 输入

必须接收 `subagent_task.schema.yaml` v2 的 `OPERATION_WITH_VALIDATOR` task unit，并与：

```text
validator: chain_and_component_selection_validator
```

组成一个上下文连续 task unit。

任务必须提供：

- 唯一源 STRUCTURE file record；
- 1.2 `classification_result.yaml`；
- 符合本 Skill schema 的 `selection_spec.yaml`；
- 1.2 report 和 resolved decision IDs；
- allowed read/write paths；
- forbidden management paths；
- Operation report、manifest、mapping 和 Validator detail paths；
- 一个输出结构路径。

`selection_spec.yaml` 应作为不可变 task input 传递，不能由 Operation 根据对话自行创建。

# 前置 gate

必须满足：

- 1.2 Validator 执行结果为 DONE；
- classification outcome 为 `CLASSIFIED_CLEAR | CLASSIFIED_WITH_WARNINGS`，或所有 blocking classification decisions 已解决并反映到新的 classification/spec；
- selection spec 的 task/workstream/source/classification hashes 一致；
- `selected_model_id` 存在；
- `selected_component_ids` 非空且全部存在；
- 所有影响选择的 decision IDs 已写入 spec；
- output format 和 output path 已明确；
- output path 位于 allowed write paths；
- 不存在源/目标同路径或跨 task 覆盖冲突。

任一 gate 不满足时返回 `BLOCKED`，不得产生部分候选结构。

# Selection spec

权威 schema：

```text
schemas/selection_spec.schema.yaml
```

核心字段：

```yaml
schema_version: 1
task_id:
workstream_id:
source_structure:
  path:
  sha256:
classification_result:
  path:
  sha256:
selected_model_id:
selected_component_ids: []
resolved_decision_ids: []
output:
  path:
  format: PDB | MMCIF
policies:
  selection_level: COMPONENT_ONLY
  covalent_closure: REQUIRE_COMPLETE
  preserve_all_atoms: true
  preserve_all_altlocs: true
  preserve_source_order: true
  preserve_coordinates: true
```

v1 不支持 residue-range、atom-level、distance-based 或 role-based implicit selection。

# 选择规则

## 明确选择

实际保留 residues 是所有 `selected_component_ids` 在 classification result 中列出的 `residue_ids` 并集。

不得：

- 根据 chain name 模糊匹配；
- 根据 residue name 批量匹配；
- 根据 component role 自动纳入；
- 根据“常见 MD 做法”删除水或离子；
- 选择 classification result 中不存在的对象。

## 共价闭包

若显式连接关系为：

```text
COVALENT | DISULFIDE | GLYCOSIDIC
```

且连接两端分属选择集与排除集，selection spec 无效。

Operation 必须：

- 返回 `SELECTION_BREAKS_CONFIRMED_COVALENT_LINK`；
- 生成 blocking confirmation item；
- 不自动扩展选择；
- 不切断连接；
- 不写候选结构。

用户可重新选择完整共价闭包，或在其他专门步骤明确处理化学断键。

金属配位、氢键、盐桥和 geometry-only covalent candidate 不构成共价闭包，但必须在 report 中列出被选择切分的关系。

## 模型

只输出 `selected_model_id` 对应模型。多模型选择必须在 spec 中明确；Operation 不默认使用第一个模型。

## Atom 保留

对每个选中 residue：

- 保留全部 atoms；
- 保留全部 altLoc；
- 保留 atom order；
- 保留坐标、occupancy、B factor、element 和 charge；
- 不做 atom-level filtering。

# 输出格式

v1 支持：

```text
PDB
MMCIF
```

format 必须由 selection spec 明确指定。

- PDB 输出只有在现有 identifiers 可无损表示时允许；
- 无法无损表示时返回 `OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS`；
- MMCIF 输出可以规范化 category 排列，但必须保留选中坐标对象和身份映射；
- AF3 CIF 选择输出写为 MMCIF，原始 AF3 专有 categories 不保证全部复制，必须在 report 中明确；
- 源文件始终保留，不被覆盖。

# 输出目录

默认：

```text
01_structure_preparation/03_chain_and_component_selection/
├── selected_structure.pdb | selected_structure.cif
├── selection_spec.yaml                 # 引用或受控副本，可选
├── selection_manifest.yaml
├── selection_mapping.yaml
├── chain_and_component_selection_report.yaml
└── selection.log                       # 可选
```

`selection_manifest.yaml` 至少记录：

- task/workstream IDs；
- source/classification/spec hashes；
- selected model；
- requested and actual component IDs；
- selected/excluded residue IDs；
- selected/excluded atom counts；
- preserved and removed explicit relations；
- split coordination/candidate relations；
- output file identity；
- applied policies；
- warning 和 decision provenance。

`selection_mapping.yaml` 必须给出每个输出 atom 到源 atom 的一对一身份映射，不依赖 atom serial 保持不变。

# 执行流程

1. 解析 task、权限和 resolved decisions；
2. 读取并 schema-validate selection spec；
3. 核验源 STRUCTURE、classification result 和 hashes；
4. 解析 selected model/component IDs；
5. 展开 selected residues 和 atoms；
6. 检查 confirmed covalent closure；
7. 汇总被切分的 coordination/geometry-only candidate 关系；
8. 检查 output format 是否可保留 identifiers；
9. 在临时路径生成候选结构、manifest、mapping 和 report；
10. 重新读取候选结构并完成最小 parse/hash 检查；
11. 原子提交业务输出；
12. 返回 Operation result，随后由专属 Validator 核验。

# Outcome codes

- `SELECTION_APPLIED`；
- `SELECTION_APPLIED_WITH_WARNINGS`；
- `SELECTION_SPEC_MISSING_OR_INVALID`；
- `SELECTION_REFERENCES_UNKNOWN_OBJECT`；
- `SELECTION_BREAKS_CONFIRMED_COVALENT_LINK`；
- `OUTPUT_FORMAT_CANNOT_PRESERVE_IDENTIFIERS`；
- `SOURCE_OR_CLASSIFICATION_HASH_MISMATCH`；
- `OUTPUT_CONFLICT`；
- `SELECTION_INTERNAL_FAILURE`。

# Artifact candidate

Operation 成功时返回一个 STRUCTURE artifact candidate，文件包括：

- selected structure；
- selection manifest；
- selection mapping；
- Operation report。

其状态仍是 `present_unvalidated`。只有专属 Validator 通过后，Manager 才能登记为本 substep 的有效候选。

# 失败与清理

- BLOCKED：不创建候选结构；可保留最小 decision diagnostic；
- FAILED：清理未完成临时文件，保留结构化 failure；
- 不覆盖其他 task 的输出；
- 同一 task 的幂等复用必须核验所有输出 hash；
- 源结构和 classification result 始终只读。

# 自检

- [ ] selection spec 是显式 task input；
- [ ] 没有基于自然语言或常见做法猜测选择；
- [ ] selected model/component IDs 全部可解析；
- [ ] 没有切断 confirmed covalent connection；
- [ ] coordination 没有被误作共价闭包；
- [ ] 选中 residues 的全部 atoms/altLoc 已保留；
- [ ] identifiers 和坐标属性未被隐式修改；
- [ ] source hash 未改变；
- [ ] manifest/mapping/report 已写；
- [ ] 候选结构仍为 UNVALIDATED；
- [ ] 未写管理目录；
- [ ] 未自行宣布 Validator 通过。
