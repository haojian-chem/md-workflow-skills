# Component and residue classification scripts

本目录包含 1.2 Validator 独有的确定性入口和内部模块。

## 公开入口

```text
inspect_model_scope.py
classify_structure.py
check_possible_connections.py
check_possible_coordination.py
build_classification_result.py
build_subagent_result.py
```

`classification_common.py`、`relation_common.py`、`rtp_reference.py`、`ccd_reference.py` 是内部模块，不作为独立 task 入口。

## 执行顺序

```text
inspect_model_scope.py
→ selected model
→ classify_structure.py
→ check_possible_connections.py
→ check_possible_coordination.py
→ build_classification_result.py
→ build_subagent_result.py
```

所有正式入口在写出前校验输入哈希和对应本地 schema。输出使用临时文件加 `os.replace()` 原子提交。

## 依赖

```text
gemmi>=0.7,<0.8
PyYAML>=6,<7
jsonschema>=4.20,<5
```

## 示例调用

```bash
python scripts/inspect_model_scope.py \
  --structure input.cif \
  --structure-sha256 <sha256> \
  --source-format MMCIF \
  --output model_scope.yaml \
  --schema schemas/model_scope.schema.yaml
```

完整分类使用 YAML 配置：

```bash
python scripts/classify_structure.py \
  --config classify_config.yaml \
  --observations classification_observations.yaml \
  --manifest reference_manifest.yaml \
  --observations-schema schemas/classification_observations.schema.yaml \
  --manifest-schema schemas/reference_manifest.schema.yaml
```

关系检查和整合工具同样使用 `--config`，并显式提供 definition/result schema 与输出路径。工具不会扫描项目目录猜测输入。

## 名称和文件安全

- residue/atom/CCD ID 严格区分大小写；
- 不允许 symlink 输入作为正式参考；
- CCD 文件名必须通过路径安全检查；
- 远程下载只在 `DOWNLOAD_MISSING` 策略下发生；
- 指定本地 CCD 目录在联网前检查；
- 输入结构不修改。
