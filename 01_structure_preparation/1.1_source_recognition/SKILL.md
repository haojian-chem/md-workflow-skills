---
name: source_recognition
description: Stage 1.1 Structure source recognition。对当前任务中明确且有界的本地 PDB/mmCIF/CIF 候选确定一个正式结构来源，安全归位并校验 SHA-256；不下载结构、不修改结构内容、不进行结构科学质量判断。
---

# 1.1 Structure source recognition

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 仅补充 1.1-specific 的对象、reuse、执行、validation 与 results 规则。

## Purpose

为当前任务建立后续 Stage 1 可直接消费的明确结构来源：

```text
有界本地候选
→ 基础格式 / identity 检查
→ 唯一选择来源
→ 默认安全复制到当前 Task 1.1 目录
→ source / destination SHA-256 核验
→ 写正式来源识别报告
```

1.1 只负责来源识别与归位，不判断结构科学质量，也不处理 chain selection、altloc、缺失区域、质子化、编号或 atom order。

## Object requirements

当前 Task Sheet 的 1.1 `对象` 必须明确限定候选范围，例如：

- 一个明确的本地 `.pdb`、`.cif` 或 `.mmcif`；
- 多个明确列出的本地候选；
- 一个明确的有界候选目录。

不能只给整个项目根目录、未限制的递归搜索范围、尚未下载的 URL 或与结构来源无关的二进制文件。

没有明确有界候选范围时向用户确认，不扫描整个项目猜来源。

## Reuse conditions

开始 1.1 时，在 `project_result_index.md` 中检索已有正式 `source_recognition_report.yaml`。

只有以下条件都明确成立时才自动复用：

1. 当前源文件 SHA-256 与旧报告 `source_sha256` 相同；
2. 旧报告指向的正式 destination 仍存在且可读；
3. destination 当前 SHA-256 与旧报告 `destination_sha256` 相同；
4. 当前请求没有改变来源选择或文件动作语义；
5. 用户没有明确要求重新识别、复制、检查或生成对照。

明确不等价时重新执行；缺少判断等价所需的信息时向用户确认。

确认复用时直接引用原正式结构和报告，不复制副本，也不创建当前 Task 空的 1.1 目录。

## Execution guidance

候选发现、自动 / 人工选择、copy / move、destination collision 和来源报告详细规则按需读取：

`references/source_selection_and_materialization.md`

主线：

1. 读取当前 Task Sheet 中 1.1 的对象和预留工作目录；
2. 先做 reuse 判断；
3. 需要新执行时，检查当前有界候选的基础格式并计算 SHA-256；
4. 无歧义时唯一选择来源；存在多个合理选择时向用户确认；
5. 创建当前 Task 专属 1.1 工作目录；
6. 默认 copy，只有用户明确授权具体 move 时才移动；
7. 校验 source / destination SHA-256；
8. 写 `source_recognition_report.yaml`；
9. validation 通过后更新 Task Sheet 与 `project_result_index.md`。

确定性 shell / Python 文件操作可用于 copy/hash/report writing；不需要为了这些动作构造 Legacy task/result/route/event 对象。

## Work directory

基础目录：

```text
<project_root>/01_structure_preparation/01_source_recognition/
```

需要本地执行时创建：

```text
<project_root>/01_structure_preparation/01_source_recognition/<task_id>/
```

只有 reuse 判断确认需要执行新的 1.1 时才创建 task-specific directory。

## Validation requirements

1.1 只有同时满足以下条件才可标记 `已完成`：

- 已唯一确定一个有效来源；
- source 仍可读取；
- 正式 destination 存在且可读取；
- `source_sha256 == destination_sha256`；
- 没有覆盖已有不同内容文件；
- `source_recognition_report.yaml` 与实际 source / destination / action / hash 一致；
- 如果实际执行 move，用户已明确授权该具体 move。

Validation 不做结构科学质量判定。

## Official results

实际执行新的 1.1 时，正式结果包括：

```text
<task_work_directory>/<source_basename>
<task_work_directory>/source_recognition_report.yaml
```

两者记录到 Task Sheet `主要结果`，并登记到 `project_result_index.md` 的 1.1 部分。

跨任务直接复用时，当前任务直接指向已有正式结果，不生成副本。

普通 debug log、临时文件和 shell 输出不是 official results。

## Safety boundary

1.1 不：

- 从 RCSB、AlphaFold Server、期刊数据库或其他网络来源下载结构；
- 修改结构内容或格式；
- 默认移动或删除源文件；
- 覆盖不同内容的 destination；
- 扫描整个项目寻找“可能结构”；
- 把来源归位成功解释成结构科学有效；
- 创建 Legacy Workstream / route / event / runtime task/result records。
