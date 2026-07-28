# Component and residue classification v1.2 redesign implementation

更新日期：2026-07-28

## 状态

```text
REDESIGN_IMPLEMENTATION_COMPLETE
CONTRACT_AND_CONTENT_OWNERSHIP_FROZEN
ALL_REPOSITORY_CONTROLLED_VALIDATION_PASSED
REAL_AF3_ACCEPTANCE_PENDING_INPUT
VALIDATOR_V1_2_OVERALL_NOT_PASSED
```

1.2 的设计、代码、schema、文档、公开入口、真实 PDB/mmCIF/GROMACS 验收、Authoring 静态检查和 Manager task closure 均已完成。当前唯一未完成项是缺少真实 AlphaFold 3 `*_model.cif` 及其对应输入序列参考，因此整体状态仍保持 `NOT_PASSED`。

完整证据见：

```text
04_evals/component_and_residue_classification_validator/VALIDATION.md
```

## 当前运行路径

```text
inspect_model_scope.py
→ model_scope.yaml

classify_structure.py
→ classification_engine.py facade
→ classification_engine_core.py
→ classification_observations.yaml
→ reference_manifest.yaml

check_possible_connections.py
→ possible_connections_result.yaml

check_possible_coordination.py
→ possible_coordination_result.yaml

build_classification_result.py
→ confirmation_requests.yaml
→ classification_result.yaml
→ classification_report.md

build_subagent_result.py
→ subagent_result v2 candidate

Manager
→ one FAST validation
→ atomic commit
→ terminal event / Workstream state
→ visible task closure
```

## 已完成实现

### 模型与精确名称

- 单 model 自动选择；
- 多 model 在正式分类前形成用户选择 barrier；
- residue/atom names 原样、区分大小写；
- 禁止 `.upper()`、alias、正则和模糊名称匹配；
- `REGISTRY` 与 `FORCE_FIELD_ANALYSIS` 使用不同且冻结的来源顺序。

### 分类与分组

- 项目定义、Skill registry、RTP 和 entity context 的确定性整合；
- project/registry 或 project/RTP conflict 完整扫描后统一确认；
- structural entity/polymer facts 决定 baseline chain grouping；
- classification conflict 不会把 polymer/branched residue 拆成 independent component；
- grouping 后恢复原 classification，不静默解决科学冲突。

### 缺失残基

- PDB `SEQRES + REMARK 465`；
- mmCIF entity sequence + unobserved-residue metadata；
- author `source_resid` 和 insertion code；
- AF3 FASTA/JSON 显式序列参考；
- author ID 或 chain 无法映射时使用 `MAPPING_UNRESOLVED`；
- 跨阶段同一 unresolved observation 合并并保留全部 evidence；
- PDB `REMARK 465` 固定列严格解析，不把说明文字识别为伪记录。

### 重原子与参考

- registry 模式使用 CCD；
- force-field 模式标准残基使用 exact RTP；
- 非标准残基使用 CCD；
- 多 altLoc 标记 `MULTIPLE_CONFORMATIONS` 并跳过重原子比较；
- 非水 exact RTP 重复定义形成确认项；
- 普通水重复 RTP 是明确例外；
- terminal RTP 必须通过显式 mapping；
- 不使用 `.n.tdb/.c.tdb` 合成端基模板；
- 项目 CCD snapshot 优先；
- 相同哈希本地候选合并；
- 不同有效本地 CCD 候选统一确认；
- shared CCD cache 和按策略下载已实现。

### 关系与 topology effect

- possible covalent connection 与 coordination 分离检查；
- geometry candidate 不自动确认；
- explicit PDB/mmCIF relations 可形成 `CONFIRMED_BY_STRUCTURE`；
- Mg/Zn `promote_nonstandard_to_linked=false` 只记录 relation；
- HEM–CYS/HIE `promote_nonstandard_to_linked=true` 经确认后才并入 polymer chain；
- confirmation file hash 绑定决定重放；
- final `chain_groups` 和 topology class 确定性重建。

### 共享结果与 Manager closure

- `classification_result.result_status` 与 `confirmation_requests.status` 是 wrapper 权威状态源；
- wrapper 生成 shared `subagent_result v2`；
- Validator 不修改 `00_project_state/**` 和 `00_project_records/**`；
- Manager 对 result/state/event candidates 执行一次 FAST；
- schema 和直接引用检查通过后原子提交；
- 写一个 terminal task event；
- 更新 Workstream current position；
- 在启动下一 task 前输出 task closure summary。

## 验收证据摘要

```text
synthetic: 59 passed
real PDB: 3 passed
real mmCIF: 3 passed
real GROMACS force field: 1 passed
authoring static checks: passed
Manager closure: passed
```

详细 run/job/artifact、输入 SHA-256 和真实结构发现统一记录于 `VALIDATION.md`。

## 已退出的旧路径

```text
references/standard_residue_alias_registry.yaml
references/coordination_detection_registry.yaml
schemas/classification_outputs.schema.yaml
```

旧行为不再属于正式运行路径：

- 名称统一转大写；
- alias/模糊匹配；
- 单脚本同时执行 model、分类、关系和最终整合；
- 内置 coordination registry 扫描；
- 单一旧输出 schema；
- 旧 `ambiguities/outcome_code` wrapper。

## 唯一剩余验收

```text
actual AlphaFold 3 *_model.cif
+
对应 fold_input.json / AlphaFold Server JSON / FASTA / 等价序列参考
```

普通 RCSB mmCIF 不得改名后冒充 AF3 输出。收到真实文件后补充 real-AF3 workflow/test 和 SHA-256 记录即可；无需重新设计或迁移 1.2。

## 当前结论

```text
implementation: PASS
contracts: FROZEN
content ownership: FROZEN
repository-controlled validation: PASS
real PDB/mmCIF/GROMACS: PASS
Manager closure: PASS
real AF3: NOT_RUN — PENDING_REAL_INPUT
validator v1.2 overall: NOT_PASSED
```
