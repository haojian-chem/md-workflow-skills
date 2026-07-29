# Component and residue classification scripts

本文件只说明 1.2 确定性脚本的 CLI、模块边界、配置输入、输出文件和退出码。

科学判定语义由：

```text
../references/classification_rules.md
```

定义；Validator 编排、preflight 和 task completion 由：

```text
../SKILL.md
```

定义。禁止在本文件复制上述文件已经拥有的规则。

# Pipeline

```text
inspect_model_scope.py
→ model_scope.yaml

classify_structure.py
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
→ subagent_result.yaml
```

# 1. Model scope

```bash
python scripts/inspect_model_scope.py \
  --structure <recognized-structure.pdb-or-cif> \
  --structure-sha256 <sha256> \
  --source-format <PDB|MMCIF|AF3_CIF> \
  --output <model_scope.yaml>
```

单 model 自动返回唯一 selected model。

多 model 返回：

```text
USER_SELECTION_REQUIRED
```

完成已记录的用户选择后，使用：

```text
--selected-model-id <model_id>
```

重新执行。

selected model 未解决时，禁止启动 `classify_structure.py`。

# 2. Baseline classification

```bash
python scripts/classify_structure.py \
  --config <classification_config.yaml>
```

配置至少固定：

```text
structure path
structure SHA-256
source format
selected_model_id
classification mode
reference inputs
output paths
```

可选配置：

```text
project_residue_definitions.yaml
force-field root
terminal RTP mappings
AF3 input JSON or FASTA
CCD project snapshot
CCD local directories
shared CCD cache
retrieval policy
```

输出：

```text
classification_observations.yaml
reference_manifest.yaml
```

## 模块边界

```text
classification_engine.py
→ runtime facade
→ structural grouping invariant
→ cross-stage normalization

classification_engine_core.py
→ baseline classification implementation

structure_records.py
→ selected-model structure records

sequence_missing.py
→ sequence-reference and missing-residue evidence

rtp_reference.py
→ RTP reference parsing

ccd_reference.py
→ CCD reference handling

explicit_relations.py
→ explicit PDB/mmCIF relation evidence
```

## AlphaFold Server JSON

```text
af3_server_sequence_reference.py
```

用于兼容 `dialect: alphafoldserver` 的单 job 顶层列表。entity 未提供显式 ID 时，按 entity 顺序和 `count` 确定性生成 `A..Z, AA..` chain IDs；ligand 和 ion 占用 chain ID，但不生成 polymer sequence。

顶层列表包含多个 job 时必须拒绝解析。

# 3. Possible covalent connections

```bash
python scripts/check_possible_connections.py \
  --config <possible_connections_check_config.yaml>
```

输出：

```text
relation_checks/possible_connections_result.yaml
```

配置未提供 `possible_connections.yaml` 时，脚本必须写出 schema 合法的 `NOT_PERFORMED` 结果。

# 4. Possible metal coordination

```bash
python scripts/check_possible_coordination.py \
  --config <possible_coordination_check_config.yaml>
```

输出：

```text
relation_checks/possible_coordination_result.yaml
```

配置未提供 `possible_coordination.yaml` 时，脚本必须写出 schema 合法的 `NOT_PERFORMED` 结果。

# 5. Result integration

```bash
python scripts/build_classification_result.py \
  --config <classification_result_build_config.yaml>
```

输出：

```text
confirmation_requests.yaml
classification_result.yaml
classification_report.md
```

首次整合通常不提供 decisions。

再次整合必须使用新输出路径，并提供绑定到上一份 `confirmation_requests.yaml` exact SHA-256 的 `decision_source`。禁止覆盖旧结果或应用未绑定的决定。

# 6. Shared Validator result

```bash
python scripts/build_subagent_result.py \
  --task <task.yaml> \
  --classification-result <classification_result.yaml> \
  --confirmation-requests <confirmation_requests.yaml> \
  --report <classification_report.md> \
  --log <classification.log> \
  --output <subagent_result.yaml>
```

wrapper 必须验证本地结果 schema 和共享 `subagent_result v2` contract。

# I/O invariants

所有公开脚本必须：

- 使用显式输入路径和输出路径；
- 核验声明 SHA-256 与实际文件内容；
- 核验 selected-model identity；
- 使用严格 YAML duplicate-key parsing；
- 使用 Draft 2020-12 schema validation；
- 使用原子写入；
- 拒绝覆盖已有不同内容的结果；
- 在技术无效时停止并返回非零退出码。

禁止脚本修改输入 STRUCTURE 文件或写入未声明路径。

# Exit codes

```text
0  deterministic processing completed
2  technical/configuration/schema/consistency failure
3  unexpected internal failure
```

退出码 `0` 只表示确定性处理完成；对象是否存在待确认问题由机器可读结果表达。

# Dependencies

安装 `requirements.txt` 声明的版本。
