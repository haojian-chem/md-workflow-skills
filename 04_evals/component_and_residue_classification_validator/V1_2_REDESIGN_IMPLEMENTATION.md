# Component and residue classification v1.2 redesign implementation

更新日期：2026-07-28

## 状态

```text
REDESIGN_IMPLEMENTATION_COMPLETE_REAL_VALIDATION_PENDING
```

新版确定性流水线已经接管 1.2 的公开脚本入口、最终结果整合和共享 `subagent_result v2` 包装路径，并通过当前完整合成测试套件的 GitHub Actions 验证。实现和合成测试通过不等于最终验收通过；真实结构、真实力场和 Manager closure 尚未完成，因此 `validator v1.2 overall` 仍保持 `NOT_PASSED`。

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
→ relation_checks/possible_connections_result.yaml

check_possible_coordination.py
→ relation_checks/possible_coordination_result.yaml

build_classification_result.py
→ confirmation_requests.yaml
→ classification_result.yaml
→ classification_report.md

build_subagent_result.py
→ subagent_result v2 candidate
```

- selected model 未解决前不执行完整分类；
- selected model 确定后完成所有仍可执行的分类、缺失残基、重原子和关系检查；
- 科学歧义统一写入 `confirmation_requests.yaml`，不在第一项歧义处提前退出；
- structural entity/polymer 事实决定 baseline chain grouping，不因 residue classification 为 `CONFLICT` 或未解决而丢失 polymer/branched chain 身份；
- grouping 结束后恢复原 `ClassificationValue`，最终输出仍保留原分类标签、resolution status 和证据；
- 缺失残基无法建立 author `source_resid` 或目标 chain 归属时，检查状态为 `MAPPING_UNRESOLVED`，不得伪装成已经生成正式缺失残基记录；
- 同一 `issue_type + subject + resolution_status` 在不同阶段重复出现时合并为一个 unresolved observation，并保留全部证据；
- wrapper 以 `classification_result.result_status` 和 `confirmation_requests.status` 为权威状态来源；
- Manager 仍是共享项目状态和记录的唯一提交者。

## 已完成的设计落地

### 输入与输出 schema

```text
schemas/project_residue_definitions.schema.yaml
schemas/possible_connections.schema.yaml
schemas/possible_coordination.schema.yaml
schemas/model_scope.schema.yaml
schemas/classification_observations.schema.yaml
schemas/reference_manifest.schema.yaml
schemas/possible_connections_result.schema.yaml
schemas/possible_coordination_result.schema.yaml
schemas/confirmation_requests.schema.yaml
schemas/classification_result.schema.yaml
```

### 严格名称 registry

```text
references/standard_residue_registry.yaml
references/covalently_linked_nonstandard_residue_registry.yaml
```

两个 registry 均采用严格、区分大小写、一个精确残基名一条定义的列表格式。项目级定义与 Skill registry 或 RTP 冲突时，完整扫描后统一请求确认，不执行 alias、正则或模糊名称覆盖。

### 确定性脚本与内部模块

```text
scripts/inspect_model_scope.py
scripts/classify_structure.py
scripts/classification_engine.py
scripts/classification_engine_core.py
scripts/classification_common.py
scripts/structure_records.py
scripts/explicit_relations.py
scripts/rtp_reference.py
scripts/ccd_reference.py
scripts/sequence_missing.py
scripts/check_possible_connections.py
scripts/check_possible_coordination.py
scripts/build_classification_result.py
scripts/build_subagent_result.py
```

已实现：

- 单 model 自动选择、多 model 用户选择 barrier 和受控写回；
- `REGISTRY` 与 `FORCE_FIELD_ANALYSIS` 两种分类模式；
- 精确、区分大小写的项目定义、Skill registry 和 RTP 解析；
- 显式 terminal-template mapping；
- PDB/mmCIF 缺失残基证据和 AF3 显式序列参考路径；
- 缺失残基 author 编号与 chain 归属无法映射时的统一 unresolved 输出；
- 跨阶段重复 unresolved observation 合并与证据保留；
- CCD 项目 snapshot、本地目录、共享 cache 和按策略下载；
- 相同哈希的本地 CCD 候选合并、不同有效本地候选统一确认；
- 项目 CCD snapshot 对后续本地来源保持权威优先级；
- 单构象残基的 CCD/RTP 重原子核验；
- 多 altLoc 残基跳过重原子比较；
- 非水 exact RTP 重复定义形成确认项，普通水重复 RTP 作为明确例外；
- 项目定义驱动的可能共价连接和金属配位检查；
- 已确认 relation 的 topology effect 与最终 `chain_groups` 重建；
- 结构 chain grouping 与 residue topology classification 解耦；
- 与上一份 confirmation 文件哈希绑定的决定重放；
- 新版最终结果到共享 `subagent_result v2` 的确定性包装。

### 测试与 CI

已纳入：

```text
.github/workflows/component-classification-v1-2.yml
```

测试集合：

```text
04_evals/component_and_residue_classification_validator/test_inspect_model_scope.py
04_evals/component_and_residue_classification_validator/test_classify_structure.py
04_evals/component_and_residue_classification_validator/test_build_subagent_result.py
04_evals/component_and_residue_classification_validator/test_v1_2_redesign_foundation.py
04_evals/component_and_residue_classification_validator/test_v1_2_relations_and_builder.py
04_evals/component_and_residue_classification_validator/test_v1_2_classification_engine.py
04_evals/component_and_residue_classification_validator/test_v1_2_polymer_grouping_conflict.py
04_evals/component_and_residue_classification_validator/test_v1_2_missing_residue_paths.py
04_evals/component_and_residue_classification_validator/test_v1_2_altloc_rtp_ccd.py
04_evals/component_and_residue_classification_validator/test_v1_2_terminal_rtp.py
```

当前覆盖：

```text
单/多 model 与输入哈希失败
公开 classify_structure.py CLI
shared result wrapper clear/pending 两条路径
schema meta-validation 与 strict registry
可能共价连接候选
HEM–CYS 配位确认后的 topology promotion
REGISTRY 大小写严格匹配与本地 CCD 优先级
FORCE_FIELD_ANALYSIS RTP 重原子缺失
N/C terminal RTP template selection
polymer entity + classification conflict 仍保持 POLYMER_CHAIN
explicit nonpolymer entity 不被错误 polymer 标签提升
PDB SEQRES + REMARK 465 缺失残基记录
mmCIF unobserved residue + author source_resid 映射
mmCIF 缺少 auth_seq_id 时 source_resid unresolved
PDB 缺失记录指向不存在 chain 时 chain unresolved
AF3 CIF + FASTA 精确序列参考
AF3 CIF + AF3 input JSON 精确序列参考
AF3 更长序列导致 author source_resid unresolved
AF3 sequence reference chain ID 严格匹配
多 altLoc 残基跳过重原子比较
非水 exact RTP 重复定义确认
普通水重复 RTP 例外
相同哈希本地 CCD 候选合并
不同有效本地 CCD 候选确认
项目 CCD snapshot 权威优先级
shared CCD cache fallback
```

最新完整合成测试证据：

```text
GitHub Actions run: 30319294167
job: 90151595691
conclusion: success
```

该运行在同一次 Actions job 中覆盖当前全部 v1.2 合成测试，包括 polymer grouping、缺失残基与 AF3 序列参考、altLoc、重复 RTP、水模型例外及 CCD 多来源矩阵。它证明合成 fixtures、schema meta-validation 与既有回归同时通过，但不替代真实 PDB/mmCIF/AF3、真实力场和 Manager closure 验收。

### 文档迁移

```text
SKILL.md
references/classification_rules.md
scripts/README.md
00_authoring/content_maps/component_and_residue_classification_validator.yaml
```

### 已退出并删除的旧运行路径

```text
references/standard_residue_alias_registry.yaml
references/coordination_detection_registry.yaml
schemas/classification_outputs.schema.yaml
```

已删除的旧行为包括：

```text
残基名统一转大写
alias/模糊名称匹配
单脚本同时完成 model、分类、共价、配位和最终整合
内置 coordination registry 自动扫描
旧单一 classification_outputs.schema.yaml 作为唯一输出
旧 ambiguities/outcome_code 驱动的 subagent wrapper
```

## 尚需完成的正式验收

```text
1. 扩展 Mg/Zn promote=false 与 HEM–CYS/HIE promote=true 的关系测试；
2. 使用真实 PDB 验证 model、缺失残基、CCD 和连接记录路径；
3. 使用真实 mmCIF 验证 entity、作者编号、unobserved residues 和 struct_conn 路径；
4. 使用 AF3 CIF + AF3 input JSON/FASTA 验证显式序列参考路径；
5. 验证真实 GROMACS force field，包括内部和端基 RTP；
6. 运行 authoring 静态检查；
7. 完成一次 Manager task → wrapper → FAST validation → closure 端到端测试；
8. 更新 SYNC_STATUS、inventory 和最终 VALIDATION 记录。
```

## 当前验收结论

```text
model scope entry: IMPLEMENTED, LATEST SYNTHETIC CI PASSED
new schemas: AUTHORED_AND_REFERENCED, META-VALIDATION PASSED IN LATEST CI
classification parser: MIGRATED_TO_V1_2, GROUPING/MISSING/ALTLOC/RTP/CCD REGRESSIONS PASSED
relation checkers: IMPLEMENTED, LATEST SYNTHETIC CI PASSED
final result builder: IMPLEMENTED, LATEST SYNTHETIC CI PASSED
subagent result wrapper: MIGRATED_TO_V1_2, LATEST SYNTHETIC CI PASSED
documentation: MIGRATED_TO_V1_2
legacy runtime path: REMOVED
latest full synthetic CI: PASSED
real-file acceptance: NOT COMPLETE
Manager closure: NOT COMPLETE
validator v1.2 overall: NOT_PASSED
```
