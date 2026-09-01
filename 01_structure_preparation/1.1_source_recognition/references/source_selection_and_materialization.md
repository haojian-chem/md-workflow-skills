# 1.1 source selection and materialization rules

Status: CURRENT

本 reference 拥有 1.1 中候选发现、来源选择、文件归位、冲突处理和来源报告的详细规则。主 `SKILL.md` 只保留何时读取本 reference 以及 1.1 的主线。

## Supported local sources

支持当前已经存在的本地结构文件：

- PDB：`.pdb`；
- PDBx/mmCIF：`.cif`、`.mmcif`；
- AlphaFold 3 输出 CIF；
- 已由用户或上游工作放到本地的 RCSB PDB/mmCIF。

扩展名本身不足以判定有效。候选至少检查：

- 路径存在；
- 是普通文件；
- 非空；
- 可读；
- 基础文本标记与 PDB 或 CIF 相符；
- 位于当前明确的有界读取范围内。

1.1 不在这里进行链完整性、几何质量、残基合理性等科学质量检查。

## Candidate discovery

优先使用当前 Task Sheet `对象` 中明确列出的文件。

如果对象是一个有界目录，默认只检查该目录顶层：

```text
*.pdb
*.cif
*.mmcif
```

不得默认递归子目录。用户明确要求递归检查时，必须限定根目录和合理搜索深度，不做无界项目扫描。

每个候选至少能够记录：

- candidate ID；
- 原始完整路径；
- basename；
- source label；
- size bytes；
- SHA-256；
- 基础格式检查结果；
- 排除理由（如有）。

可使用的 source label 示例：

```text
PDB_LOCAL
RCSB_PDB
RCSB_MMCIF
AF3_CIF
MMCIF_LOCAL
UNKNOWN_CIF
```

source label 只是来源描述，不代表结构科学质量。

## Source selection

可以自动选择的情况只有：

- 当前对象明确指定一个有效文件；或
- 当前有界候选范围内只有一个有效候选，且与用户描述没有冲突。

以下情况必须由当前用户可见 Agent 确认：

- 多个有效候选且无法唯一确定；
- 同一体系存在不同来源版本；
- 文件名相同但 SHA-256 不同；
- 用户描述和候选内容 / 路径冲突；
- 选择不同候选代表不同研究对象或处理方案。

确认前不把任何候选写成正式 1.1 结果。

## Work directory

1.1 稳定基础目录：

```text
<project_root>/01_structure_preparation/01_source_recognition/
```

当前 Task Sheet 实际执行目录：

```text
<project_root>/01_structure_preparation/01_source_recognition/<task_id>/
```

这里的 `<task_id>` 是当前 Task Sheet 的 `Txxxx` 标识。

Manager 只记录该未来路径，不创建 `<task_id>/`。Task Execution Agent 先完成 reuse 判断；只有确实需要新的 1.1 执行时才创建当前 Task Sheet 的工作目录。

## Default materialization: copy

选定来源后默认字节复制到：

```text
<project_root>/01_structure_preparation/01_source_recognition/<task_id>/<source_basename>
```

规则：

- 不修改源文件；
- 不删除源文件；
- 不用符号链接代替正式复制结果；
- 不覆盖已有不同内容目标；
- 复制前计算 source SHA-256；
- 复制后计算 destination SHA-256；
- source / destination SHA-256 必须相同。

## Existing destination

当前 Task Sheet 工作目录中目标文件已存在时：

- SHA-256 与源相同：直接使用已有目标，不重复复制；
- SHA-256 与源不同：不覆盖，向用户说明冲突并确认后续处理；
- 目标不可读或无法安全核验：停止写入，1.1 保持 `未完成`。

不能为了绕开冲突自动追加后缀生成新的正式文件名。

其它 Task Sheet 工作目录中的同名文件不属于当前 Task Sheet 的 destination collision；若其中已有正式结果可能满足当前需求，按当前 1.1 reuse 规则判断，而不是按文件名直接复用。

## Controlled move

只有用户明确要求移动某个具体源文件时才考虑 move，并且同时确认：

- 用户明确授权移动该具体文件；
- 源目录允许写入；
- 源不属于受保护的 `01_sources/`；
- destination collision 已解决；
- move 不违反项目文件保护规则。

任一条件不满足时保持默认 copy，不自行 move。

## Source-recognition report

当前 Task Sheet 实际执行时正式报告路径：

```text
<project_root>/01_structure_preparation/01_source_recognition/<task_id>/source_recognition_report.yaml
```

报告应足以独立说明：

```text
selected candidate
source label
source path
source SHA-256
action: COPIED | MOVED | REUSED_IDENTICAL_COPY
destination path
destination SHA-256
candidate / exclusion summary
warnings
```

字段可以根据当前实现保持轻量；不要为了形式完整增加 Workstream、route、artifact、runtime-task 或 transaction IDs。

## Failure and recovery

- 复制中断或 hash 不一致：删除本次创建的不完整目标，保留源文件，1.1 保持 `未完成`；
- destination collision：不覆盖，等待用户处理；
- 多候选歧义：不生成正式复制结果，等待用户选择；
- 全部候选无效：保留排除理由并保持 `未完成`；
- 旧结果 reuse 核验失败：旧结果不能作为当前 Task Sheet 的完成依据，重新执行或在信息不足时确认。

技术恢复继续使用同一 Task Sheet 的 1.1 项和同一 Task Sheet 工作目录，不建立 attempt Task Sheet 或 Legacy recovery state。
