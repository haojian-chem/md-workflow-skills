---
name: analysis-workflow
description: Stage 5 — Analysis 的 Workflow Skill。定义 5.1 Analysis planning and orchestration 的阶段边界、Manager 交接、plan-item 组织、Stage 5 索引关系与完成条件；不复制具体分析方法内部规则。
---

# 5 Analysis

## Purpose

负责 Stage 5 的阶段级科学边界与唯一 sub-stage 映射。

Stage 5 只包含：

```text
5.1 Analysis planning and orchestration
```

Stage 5 继续采用 Task Sheet sub-stage 模式。具体 RMSD、RDF、PCA、trajectory preprocessing、index generation 等不是新的 `5.x` sub-stage，而是由 5.1 在 Task Sheet 内组织的 plan items，并调度对应 analysis Skill / Tool 完成。

## Responsibility boundary

本 Workflow 负责：

- Stage 5 的阶段目标；
- `5.1` 的唯一 sub-stage 映射；
- Manager 与 5.1 的职责边界；
- Stage 5 plan-item 模型的阶段级约束；
- Stage 5 project-level indexes 的位置和维护责任；
- Stage 5 project-result 登记边界；
- Stage 5 完成条件。

本 Workflow 不负责：

- 具体分析方法选择；
- RMSD/RDF/PCA 等方法的算法或命令；
- `trjconv` / `make_ndx` 的具体执行规则；
- 各工具输出数据的 validation；
- 为 Stage 5 建立 project-level analysis-unit identity。

详细冻结架构：

`00_authoring/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

## Stage directory

项目中的 Stage 5 根目录：

```text
05_analysis/
```

5.1 的稳定基础工作目录：

```text
05_analysis/01_analysis_planning_and_orchestration/
```

Stage 5 project-level prepared-input indexes：

```text
05_analysis/indexes/
├── trajectory_index.yaml
└── ndx_index.yaml
```

`indexes/` 中保存索引文件本身；实际 trajectory / `.ndx` 的存放位置由对应 producer Tool/Skill 决定。

## Substep registry

```yaml
step_id: "5.1"
name: analysis_planning_and_orchestration
base_work_directory: 05_analysis/01_analysis_planning_and_orchestration
skills:
  operation: 02_operations/analysis_planning_and_orchestration/SKILL.md
  validator: null
```

Stage 5 不设置统一 Validator Skill。具体 tool / analysis Skill 对自己的输出负责 validation。

## Manager handoff

Manager 在新任务或显式重新规划时，如果任务范围包含 Stage 5：

- 在 Task Sheet 中建立 `5.1 Analysis planning and orchestration`；
- 原样记录用户明确提出的分析目标、分析对象和约束；
- 用户明确指定 RMSD/RDF 等方法时可以原样保留；
- 不进一步设计具体方法组合、selection、trajectory 处理或 reuse。

进入 5.1 后，再由 5.1 把这些需求展开成实际 plan items。

## Stage-internal planning relation

5.1 在 Stage 5 开始时集中：

```text
分析需求
→ tool inventory
→ 已有正式分析结果 / prepared-input indexes
→ reuse 核验
→ 当前完整 Stage 5 plan
```

plan 中可以同时包含：

- 直接使用已有输入的 analysis item；
- 需要 `trjconv` 生成 prepared trajectory 的 item；
- 需要 `make_ndx` 生成 `.ndx` 的 item；
- 具体 RMSD / RDF / PCA / 其他 analysis item。

如果当前 plan 中的前置 item 将生成后续所需文件，5.1 在规划时直接建立其用途/依赖关系，不在每个后续 item 启动前重新进行一轮全局 reuse 查询。

只有执行证据破坏当前 plan 前提时，才调整尚未完成的后续 plan。

## Plan-item model

5.1 的内部 plan item 使用局部整数编号 `1, 2, 3, ...`。

编号一旦建立原则上固定，不删除、不重编号；不再执行的项目使用 `已终止`。

状态只使用：

```text
未完成
已完成
已终止
```

每项最小记录：

```text
编号
tool
inputs
settings
status
path
```

其中：

- `tool` 引用 5.1 tool inventory 中的条目；
- `inputs` 对已有文件使用完整文件路径；
- 尚未生成的输入可直接写“使用第 N 项生成的处理后轨迹 / ndx 文件”等清楚依赖；
- `settings` 是 tool-specific，不建立 Stage 5 通用 schema；
- `path` 是当前 plan item 相关文件的完整存放目录，不指向单个结果文件。

## Resource indexes

### `trajectory_index.yaml`

由 `trjconv` Tool/Skill 维护。5.1 只查询、核验和使用。

### `ndx_index.yaml`

由 `make_ndx` Tool/Skill 维护。5.1 只查询、核验和使用。

`.ndx` reuse 的阶段级规则：

```text
same tpr
→ 可复用

different tpr + Stage 4 run_unit.yaml 中对应 run unit 使用 same top
→ 可复用

different top
→ 不复用
```

不默认追加 atom count / atom ordering 的第二层核验，也不在 `ndx_index.yaml` 中复制 groups。

## Project-result registration

Stage 5 在 `project_result_index.md` 中登记到“分析事项”粒度：

```text
分析对象
→ 分析内容
→ 详细记录入口
```

详细记录入口应能追溯到对应 Task Sheet / 5.1 plan item，并进一步定位 `tool / inputs / settings / status / path`。

不逐文件把 `.xvg/.csv/.dat/.png/.xtc/.ndx` 复制为 project-level 结果项。

## Completion condition

Stage 5 完成需要：

- 为满足当前用户目标所需的 5.1 plan items 已经完成，或有明确理由进入 `已终止`；
- 所有 `已完成` item 均已通过其对应 Tool/analysis Skill 自己负责的 validation；
- 所需分析事项已按上述边界登记到 `project_result_index.md`。

是否额外汇总多个分析结果、进行综合解释或生成报告，由当前任务要求决定，不是 Stage 5 固定完成条件。

## Skill mapping

```text
5.1
→ 02_operations/analysis_planning_and_orchestration/SKILL.md
```

具体 analysis Skill / Tool 的发现由 5.1 读取其 inventory 完成，本 Workflow 不复制该清单。
