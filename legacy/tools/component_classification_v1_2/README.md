# Retired Stage 1.2 script package

Status: LEGACY / NOT CURRENT AUTHORITY

本目录记录 2026-08-23 重新生成结构准备 1.2 前退出 active path 的旧脚本包。

旧 active path：

`01_structure_preparation/1.2_component_and_residue_classification/scripts/`

归档基线 commit：

`323a76f2039c8bdcc82b68976aa88661d80caa65`

旧 `scripts/` tree：

`a872d39356f99f20072d3aeb2b09290c87441cba`

该 tree 是旧 1.2 固定 Python 流水线的完整可执行源码快照，包含 model scope、结构分类、CCD/RTP 解析、缺失残基处理、共价连接/金属配位检查、人工决定同步、最终结果构建及依赖文件。

完整文件名与 blob SHA 清单见：

`00_authoring/archive/legacy_scientific_skills/1.2_component_and_residue_classification_2026-08-23/PACKAGE_TREE.md`

旧源码通过上述 commit + tree/blob identity 精确恢复。本目录不复制这些已退出 current architecture 的大体量脚本，以避免产生第二套可被误执行的脚本入口。

当前 1.2 只保留：

`01_structure_preparation/1.2_component_and_residue_classification/scripts/selection_identity.py`

它只负责稳定身份的机械物化，不属于本旧科学检查流水线。
