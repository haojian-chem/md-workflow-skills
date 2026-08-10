---
name: source_recognition
description: Lightweight Runtime v2 的 1.1 Source recognition。对任务单中明确且有界的本地 PDB/mmCIF/CIF 候选进行识别和选择，默认安全复制到结构准备目录并校验 SHA-256；不下载结构、不修改结构内容，也不依赖 Legacy runtime task/result/route/event 闭环。
---

# 目标

为当前任务建立后续结构准备使用的明确结构来源：

- 识别当前 1.1 对象中给出的本地结构候选；
- 在无歧义时确定一个来源；
- 默认复制到 `01_structure_preparation/01_source_recognition/`；
- 校验源文件和目标文件 SHA-256 一致；
- 保存来源、目标和候选检查信息；
- 产生可供后续环节直接消费和跨任务复用的正式结果。

本 Skill 不负责结构科学质量判定。复制成功只表示来源已经明确和归位，不表示结构已经完成结构准备验证。

# Lightweight Runtime 接口

## Purpose

确定并归位当前任务使用的初始结构来源。

## Object requirements

当前 Task Sheet 的 1.1 `对象` 必须能够明确限定候选范围，允许：

- 一个明确的本地 `.pdb`、`.cif` 或 `.mmcif` 文件；
- 多个明确列出的本地候选文件；
- 一个明确的有界候选目录，默认只检查其顶层支持格式文件。

对象不能只是：

- 整个项目根目录；
- 未限制范围的递归搜索请求；
- 一个尚未下载的网络地址；
- 轨迹、拓扑、检查点、压缩包或未知二进制文件。

如果没有明确且有界的候选范围，Task Execution Agent 直接向用户确认，不扫描整个项目猜测来源。

## Reuse conditions

开始 1.1 时，先在 `project_result_index.md` 的 1.1 已有结果中寻找可能匹配的 `source_recognition_report.yaml`。

已有 1.1 结果可以自动复用，仅当能够确认：

1. 当前要求使用的源文件 SHA-256 与已有报告的 `source_sha256` 相同；
2. 已有报告指向的正式目标结构仍存在且可读；
3. 目标结构当前 SHA-256 与报告中的 `destination_sha256` 相同；
4. 当前请求没有要求改变来源选择语义或执行不同动作；
5. 用户没有明确要求重新识别、重新复制、重新检查或做对照。

只要任一条件明确不满足，就正常执行新的 1.1。

如果已有结果可能匹配但缺少判断等价性所需的信息，不擅自复用，向用户确认。

相同 basename 不能作为复用依据；SHA-256 是内容等价性的主要依据。

## Execution rules

执行规则见下文“候选检查”“选择”“归位”和“冲突处理”。

## Validation requirements

1.1 只有同时满足以下条件才可标记为 `已完成`：

- 已唯一确定一个有效来源；
- 来源文件仍可读取；
- 正式目标结构存在且可读取；
- `source_sha256 == destination_sha256`；
- 没有覆盖已有不同内容文件；
- `source_recognition_report.yaml` 已写入且与实际来源/目标/hash 一致；
- 如果执行了移动，确有当前用户对该具体移动的明确授权。

如果无法满足这些要求，当前子环节保持或改为 `未完成`，并在 Task Sheet 的必要执行记录中写明恢复所需的信息。

## Official results

1.1 的正式结果为：

1. 选定并归位后的结构文件：
   `01_structure_preparation/01_source_recognition/<source_basename>`
2. 来源识别报告：
   `01_structure_preparation/01_source_recognition/source_recognition_report.yaml`

两者都应在当前 Task Sheet 的 1.1 `主要结果` 中记录完整路径，并登记到 `project_result_index.md` 的 1.1 部分。

普通 debug log、临时文件和 shell 输出不是 official results。

# 职责边界

负责：

- 有界候选发现与基础格式检查；
- 来源选择；
- 默认复制或明确授权下的受控移动；
- source/destination SHA-256 校验；
- 目标冲突处理；
- 写正式来源识别报告。

不负责：

- 从 RCSB、AlphaFold Server、期刊数据库或其他网络来源下载结构；
- 判断结构科学质量；
- 链/组分保留；
- altloc、缺失区域、质子化、编号或原子顺序处理；
- 修改结构内容或格式；
- 维护 route、Workstream、event、artifact state、runtime task/result；
- 为使用旧确定性 Tool 而构造 Legacy `task.yaml`；
- 扫描整个项目寻找“可能的结构”。

# 支持的来源

支持现有本地文件：

- PDB：`.pdb`；
- PDBx/mmCIF：`.cif`、`.mmcif`；
- AlphaFold 3 输出 CIF；
- 已由用户放到本地的 RCSB PDB/mmCIF。

扩展名本身不足以判定有效。候选至少应检查：

- 路径存在；
- 是普通文件；
- 非空；
- 可读；
- 基础文本标记与 PDB 或 CIF 相符；
- 候选处于当前明确的有界读取范围内。

不进行链完整性、几何质量、残基合理性等科学检查。

# 候选发现

优先使用 Task Sheet `对象` 中明确列出的文件。

如果对象是一个有界目录，默认只检查该目录顶层的：

```text
*.pdb
*.cif
*.mmcif
```

不得默认递归子目录。

如果用户明确要求递归检查，必须先限定根目录和合理搜索深度，不做无界项目扫描。

每个候选至少记录：

- candidate ID；
- 原始完整路径；
- basename；
- source label；
- size bytes；
- SHA-256；
- 基础格式检查结果；
- 排除理由，如有。

推荐 source label：

```text
PDB_LOCAL
RCSB_PDB
RCSB_MMCIF
AF3_CIF
MMCIF_LOCAL
UNKNOWN_CIF
```

source label 是来源描述，不影响结构科学质量判断。

# 来源选择

## 可以自动选择

仅在以下情况自动选择：

- 当前对象明确指定一个有效文件；或
- 当前有界候选范围内只有一个有效候选，且没有与用户描述冲突。

## 必须向用户确认

完成所有不需要用户参与的检查后，如果仍存在以下情况，Task Execution Agent 直接向用户确认：

- 多个有效候选，无法唯一确定；
- 同一体系存在不同来源版本；
- 文件名相同但 SHA-256 不同；
- 用户描述和候选内容/路径冲突；
- 选择哪一个候选本身代表不同研究对象或处理方案。

确认前不复制任一候选作为正式结果。

# 文件归位

## 默认：复制

选定来源后，默认字节复制到：

```text
<project_root>/01_structure_preparation/01_source_recognition/<source_basename>
```

硬规则：

- 不修改源文件；
- 不删除源文件；
- 不用符号链接代替正式复制结果；
- 不覆盖已有不同内容目标；
- 复制前计算 source SHA-256；
- 复制后计算 destination SHA-256；
- 两者必须相同。

需要创建工作目录时，只创建当前 1.1 标准工作目录，不顺带建立未来阶段目录。

## 已有目标

如果目标文件已存在：

- SHA-256 与源相同：直接复用该已有目标，不重复复制；
- SHA-256 与源不同：不覆盖，向用户说明冲突并确认后续处理；
- 目标不可读或无法安全核验：停止写入，本环节记为 `未完成`。

不能为了绕开冲突而自动添加后缀生成一个新的正式文件名。

## 受控移动

只有用户在当前任务中明确要求移动具体源文件时才考虑移动。

同时必须确认：

- 用户明确授权移动该具体文件；
- 源目录允许写入；
- 源不属于受保护的 `01_sources/`；
- 目标冲突已经解决；
- 移动不会违反项目文件保护规则。

未满足条件时默认保持复制，不擅自移动。

# Preflight

执行任何写入前确认：

- 当前任务单中的子环节确实是 1.1；
- 当前 `对象` 给出了明确且有界的候选；
- 工作目录是当前任务允许使用的 1.1 目录；
- 来源文件不会被默认修改或删除；
- 没有待解决的多候选歧义；
- 没有要求覆盖不同内容目标；
- move 请求已有明确授权。

Preflight 不通过时不产生业务写入。

# 执行流程

1. 读取当前 Task Sheet 中 1.1 的对象和工作目录；
2. 读取本 Skill；
3. 查询 `project_result_index.md` 中已有 1.1 结果并按 reuse conditions 判断；
4. 如果不能复用，收集当前有界候选；
5. 检查基础格式并计算 SHA-256；
6. 唯一选择来源，存在歧义时询问用户；
7. 检查目标冲突；
8. 默认复制，或在明确授权下受控移动；
9. 核验 source/destination SHA-256；
10. 写 `source_recognition_report.yaml`；
11. 按 Validation requirements 做最终核验；
12. 更新当前 Task Sheet；
13. 将 official results 登记到 `project_result_index.md`。

# 来源识别报告

正式报告路径：

`01_structure_preparation/01_source_recognition/source_recognition_report.yaml`

建议内容：

```yaml
schema_version: 2
step_id: "1.1"
task_id: T001
selected_candidate_id: candidate_001
source_label: PDB_LOCAL
source_path: /absolute/path/to/source.pdb
source_sha256: <sha256>
action: COPIED | MOVED | REUSED_IDENTICAL_COPY
destination_path: /absolute/project/path/01_structure_preparation/01_source_recognition/source.pdb
destination_sha256: <sha256>
candidates: []
excluded_candidates: []
warnings: []
```

报告不得依赖 `workstream_id`、route ID、artifact ID 或 Legacy task/result contract 才能解释。

# Lightweight Tool 使用规则

历史 `source_recognition_deterministic` Tool 的科学动作仍有价值，但当前 v0.1.0 接口依赖 Legacy `task.yaml`、subagent result 和 runtime closure。

在它获得 Lightweight-compatible 显式路径接口之前：

- 不把它作为 1.1 默认路径；
- 不为了调用它构造 Legacy runtime task；
- 可以直接使用受控的本地文件操作和 SHA-256 命令完成本 Skill 的确定性动作。

未来若 Tool 改为直接接受明确候选路径、工作目录和动作参数，可重新作为本 Skill 的默认确定性实现，但不得重新引入 route/event/transaction 依赖。

# 失败与恢复

- 复制中断或 hash 不一致：删除本次创建的不完整目标；保留源文件；本环节记为 `未完成`；
- 目标内容冲突：不覆盖；等待用户处理；
- 多候选歧义：不生成正式复制结果；等待用户选择；
- 全部候选无效：记录排除理由并保持 `未完成`；
- 已有结果复用核验失败：不得把旧结果标记为当前任务完成依据，重新执行或询问用户。

恢复时继续使用同一个 1.1 任务块，不创建 attempt task 或 Legacy recovery state。

# 自检

- [ ] 当前对象范围明确且有界；
- [ ] 已执行 1.1 复用检查；
- [ ] 未扫描整个项目；
- [ ] 默认复制而非移动；
- [ ] 未修改或删除受保护源文件；
- [ ] 未覆盖已有不同内容文件；
- [ ] source/destination SHA-256 一致；
- [ ] 多候选歧义由当前 Task Execution Agent 向用户确认；
- [ ] 未进行结构科学质量判定；
- [ ] official results 已写入 Task Sheet 和 result index；
- [ ] 未创建 Legacy task/result/route/event/artifact record。
