# Stage 1.2 pre-regeneration archive

Status: ARCHIVE / NOT CURRENT AUTHORITY

本目录保存 2026-08-23 重新生成 `1.2 Component and residue classification` 前的旧版设计与接口快照。

旧版 active path：

`01_structure_preparation/1.2_component_and_residue_classification/`

归档基线 commit：

`323a76f2039c8bdcc82b68976aa88661d80caa65`

该 commit 中旧版 1.2 的关键对象为：

```text
SKILL.md blob                 e61b40ea85048a1615b08e6cbf65866a3d153aca
references/ tree             24eec6365e3f7fc1007a125b52e34d06c5d4303b
schemas/ tree                d1c969c2758902d682bd9765f740ee495c9bc32c
scripts/ tree                a872d39356f99f20072d3aeb2b09290c87441cba
```

本归档目录直接保存旧版 main Skill、主要科学规则、正式结果 schema、reference manifest schema、脚本说明和旧 CCD library 说明；`PACKAGE_TREE.md` 锁定旧 package 的完整 tree/blob identity。未在本目录重复复制的残基登记表、CCD seed 数据或其它未修改支持文件，可通过上述 commit/tree 精确恢复。

按照当前仓库归档边界，旧可执行脚本与旧流水线 schema 的 legacy 入口分别为：

```text
legacy/tools/component_classification_v1_2/README.md
legacy/contracts/component_classification_v1_2/README.md
```

这两个 legacy 入口记录旧脚本包和旧 schema 包的精确 commit/tree/blob identity，不建立第二套可被误执行或误引用的 current authority。

该旧版的主要实现特征是以固定 Python 流水线驱动 model scope、分类、关系检查、人工决定同步和最终结果构建。新版 1.2 不应从本目录或上述 legacy 入口继承执行 authority；仅在历史审计或恢复旧项目时读取。
