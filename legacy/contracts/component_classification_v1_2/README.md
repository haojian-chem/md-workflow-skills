# Retired Stage 1.2 pipeline schemas

Status: LEGACY / NOT CURRENT AUTHORITY

本目录记录 2026-08-23 重新生成结构准备 1.2 前退出 active path 的旧流水线 schema 包。

旧 active path：

`01_structure_preparation/1.2_component_and_residue_classification/schemas/`

归档基线 commit：

`323a76f2039c8bdcc82b68976aa88661d80caa65`

旧 `schemas/` tree：

`d1c969c2758902d682bd9765f740ee495c9bc32c`

其中已退出 current architecture 的内容包括固定脚本流水线所需的 config、observations、model scope、confirmation request、独立 relation-check result 和 final-build config 等 schema。完整文件名与 blob SHA 清单见：

`00_authoring/archive/legacy_scientific_skills/1.2_component_and_residue_classification_2026-08-23/PACKAGE_TREE.md`

旧 schema 通过上述 commit + tree/blob identity 精确恢复。本目录不复制这些已经退出 current result architecture 的 contract，以避免与当前 1.2 v2 正式结果 schema 形成平行 authority。

当前有效 schema 仍位于：

`01_structure_preparation/1.2_component_and_residue_classification/schemas/`

其中 `classification_result.schema.yaml` 与 `reference_manifest.schema.yaml` 已按重新生成后的 1.2 更新；项目残基/关系定义、CCD library index 和 relation decision 等仍有当前用途的 schema 保持 active。
