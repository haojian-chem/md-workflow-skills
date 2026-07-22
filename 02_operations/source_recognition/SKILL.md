---
name: source_recognition
description: 在明确授权的输入路径中识别并选择现有 PDB、mmCIF 或 AlphaFold 3 CIF 结构文件，将选定源文件安全复制到结构准备目录并生成可追溯报告。默认不移动、不覆盖或修改原始文件；不负责联网获取结构或进行科学质量判定。
---

# 目标

为一个 Workstream 建立首个可追溯的 STRUCTURE artifact candidate：

- 识别支持的现有结构文件；
- 在无歧义时选择源文件，存在歧义时返回统一 decision request；
- 默认复制到 `01_structure_preparation/01_source_recognition/`；
- 计算复制前后 SHA-256 并确认字节一致；
- 保留原文件不变；
- 写入详细 source recognition report；
- 按 `subagent_result.schema.yaml` 返回精简 Operation result。

# 职责边界

负责：

- 在 `subagent_task` 授权的 read paths 内识别候选结构；
- 检查格式、普通文件状态、可读性和基础文件签名；
- 按任务输入或已解决用户决定选择一个源文件；
- 执行安全复制或经过明确授权的受控移动；
- 校验目标文件与源文件的一致性；
- 返回 artifact candidate 和详细报告路径。

不负责：

- 从 RCSB、AlphaFold Server、期刊数据库或其他网络来源下载文件；
- 判断结构的科学质量、链选择、组分保留、altLoc、缺失区域或质子化；
- 修改结构内容、原子顺序、编号或格式；
- 创建 Workstream、路线、artifact record 或项目状态；
- 写入 `00_project_state/**` 或 `00_project_records/**`；
- 直接向用户提问；
- 创建其他子 Agent。

# 输入

必须接收符合：

`03_contracts/subagent_task.schema.yaml`

的 OPERATION task unit。

任务至少应提供：

- `task_id`、`workstream_id`、`workflow_name`；
- `work_directory`；
- `allowed_read_paths`；
- `allowed_write_paths`；
- `forbidden_paths`，必须包含项目状态和记录目录；
- 显式候选路径、候选目录或上游候选摘要；
- 已解决用户决定；
- 预期输出和 detail log 位置。

没有任何明确候选路径或有界候选目录时返回 BLOCKED，不进行全项目无界递归扫描。

# 支持的来源

支持现有本地文件：

- PDB：`.pdb`；
- PDBx/mmCIF：`.cif`、`.mmcif`；
- AlphaFold 3 输出 CIF：`.cif`，通过文件内容和上游来源信息标记为 AF3；
- RCSB 提供的本地 PDB/mmCIF 文件。

不根据扩展名 alone 判定成功。至少检查：

- 是普通文件而不是目录；
- 文件非空；
- 文件可读；
- 文本可解析到与 PDB 或 CIF 相符的基础标记；
- 文件路径位于 allowed read paths 内。

压缩包、轨迹、拓扑、坐标检查点和未知二进制文件不属于本 Operation。

# 候选发现

优先级：

1. task 明确指定的 source path；
2. 已解决 decision 指定的 candidate ID；
3. task 明确列出的 candidate paths；
4. task 指定的有界候选目录的顶层文件。

默认不递归进入任意深度子目录。需要递归时，task 必须明确给出根目录、最大深度和允许扩展名。

每个候选记录：

- candidate ID；
- 原始路径；
- basename；
- source label：`PDB_LOCAL | RCSB_PDB | RCSB_MMCIF | AF3_CIF | MMCIF_LOCAL | UNKNOWN_CIF`；
- size bytes；
- modified time；
- SHA-256；
- 基础格式检查结果；
- 排除理由，如有。

# 候选选择

## 可自动选择

仅在以下情况自动选择：

- task 显式指定一个有效文件；或
- 只有一个有效候选，且没有与上游摘要冲突。

## 必须请求用户决定

以下情况不自动选择：

- 多个有效候选且无法由已解决决定唯一确定；
- 同一体系存在 PDB 与 mmCIF/AF3 等不同来源版本；
- 文件名相同但 SHA-256 不同；
- 上游说明与文件内容或路径不一致；
- 候选均有明显格式问题。

完成所有可执行检查后返回 `confirmation_items`。子 Agent 不直接提问。

# 文件归位规则

## 默认行为：复制

选定源文件后，默认使用字节复制到：

```text
01_structure_preparation/01_source_recognition/<source_basename>
```

硬规则：

- 不修改源文件；
- 不删除源文件；
- 不建立符号链接代替复制；
- 不覆盖已有不同内容的目标文件；
- 复制前计算源 SHA-256；
- 复制后计算目标 SHA-256；
- 两者必须一致，否则删除本次不完整目标并返回 FAILED；
- 报告中保存原始路径和复制目标路径。

## 目标文件已存在

- 目标 SHA-256 与源相同：复用现有目标，记录 `REUSED_IDENTICAL_COPY`，不重复写入；
- 目标 SHA-256 与源不同：不覆盖、不自动重命名，返回 blocking decision request；
- 无法读取现有目标：返回 BLOCKED 或 FAILED，不继续覆盖。

## 受控移动

只有同时满足以下条件才允许移动：

- 用户已明确授权移动该具体文件；
- 授权已作为 resolved decision 进入 task；
- source parent 位于 allowed write paths；
- source 不属于只读来源目录或受保护 `01_sources/`；
- 目标不存在，或与源内容完全一致且移动策略已明确；
- 移动属于本 task 的 required output。

即使允许移动，也先记录源 SHA-256，移动后核验目标 SHA-256。未满足任一条件时自动降级为复制，不得擅自移动。

# Preflight

执行前确认：

- task unit mode 为 OPERATION；
- Skill 名称和路径匹配；
- Workstream 与 Workflow 标识存在；
- work directory 位于 allowed write paths；
- 状态和记录目录位于 forbidden paths；
- 候选范围有界；
- 目标父目录可安全创建；
- 当前没有要求覆盖不同内容文件；
- move 请求有明确 resolved decision 和写权限。

Preflight 不通过时不产生业务副作用。

# 执行流程

1. 解析 task 和 resolved decisions；
2. 收集有界候选；
3. 对候选执行基础格式与 SHA-256 检查；
4. 排除无效候选并记录理由；
5. 唯一选择或返回 decision request；
6. 计算目标路径并检查冲突；
7. 默认复制，或在完整授权下受控移动；
8. 校验目标 SHA-256；
9. 写 `source_recognition_report.yaml`；
10. 返回精简结构化结果。

# 详细报告

写入：

```text
01_structure_preparation/01_source_recognition/source_recognition_report.yaml
```

报告至少包含：

```yaml
schema_version: 1
task_id:
workstream_id:
selected_candidate_id:
source_label:
source_path:
source_sha256:
action: COPIED | MOVED | REUSED_IDENTICAL_COPY
destination_path:
destination_sha256:
candidates: []
excluded_candidates: []
resolved_decisions: []
warnings: []
```

报告是业务明细，不是 artifact record。Manager 根据 subagent result 注册 artifact set。

# 返回

返回必须符合：

`03_contracts/subagent_result.schema.yaml`

Operation result 应明确：

- 执行终态；
- 选择和归位摘要；
- 新建、修改或复用的文件；
- STRUCTURE artifact candidate；
- source 与 destination SHA-256；
- confirmation items；
- warning/failure；
- report path；
- 下一步建议。

不得直接标记 STRUCTURE artifact 为 VALIDATED。初始复制结构通常是 UNVALIDATED，后续由 Validator 和 Manager 更新状态。

# 失败与清理

- 复制中断或 hash 不一致：删除本次创建的不完整目标，保留源文件，返回 FAILED；
- 移动后 hash 不一致：返回 FAILED 并停止，不进行额外自动修复；
- 目标冲突：不覆盖，返回 BLOCKED；
- 多候选歧义：不复制，返回 blocking decision request；
- 格式全部无效：返回 BLOCKED，并列出排除理由。

# 自检

- [ ] 候选范围有界；
- [ ] 源文件位于 allowed read paths；
- [ ] 默认执行复制而非移动；
- [ ] 未修改或删除原文件；
- [ ] 未覆盖不同内容的目标；
- [ ] 复制前后 SHA-256 一致；
- [ ] 多候选歧义已返回 decision request；
- [ ] 未进行科学质量判定；
- [ ] 未写项目状态或记录目录；
- [ ] 详细报告已落盘；
- [ ] 返回符合共享 subagent result contract。
