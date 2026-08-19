---
name: md-workflow-runtime
description: 真实 MD 项目的跨 Stage Task Execution runtime 入口。负责读取目标 Task Sheet、定位当前任务项、加载 current scientific Skill，并按统一规则维护任务进度、通用 reuse / validation / result registration 与后续计划更新；Stage-specific 的科学调整方式由对应 Stage / Step Skill 拥有。
---

# MD Workflow runtime

## Purpose

本 Skill 是真实 MD 项目 Task Execution 的跨 Stage 通用入口。

Manager 创建或定位 Task Sheet 后，连续科研执行从这里开始：

```text
AGENTS.md
→ 00_runtime/SKILL.md
→ target Task Sheet
→ current Stage / Step main Skill
→ 按需 references / supporting Skills / deterministic Tools
```

本 Skill 只拥有跨 Stage 的通用 runtime 机制，包括：

- Task Sheet 的读取、进度维护与最小恢复上下文；
- 普通任务项的通用状态语义；
- 通用 reuse、validation、formal-result registration 默认规则；
- 普通 task-specific directory 的创建时机；
- 执行后更新 Task Sheet 并继续下一任务项的通用机制；
- 按需读取、避免无关扫描的 runtime 约束。

本 Skill **不定义某个 Stage 应如何根据具体科研结果调整后续计划**。如果某 Stage main Skill 拥有 stage-specific orchestration / planning rules，则具体“如何调整”由该 Stage main Skill 定义；具体科研处理与结果判定继续由对应 Step / capability Skill 定义。

## Project records

真实项目默认记录：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    ├── T001.md
    └── ...
```

职责：

- `task_index.md`：任务导航和任务级状态；
- `tasks/Txxxx.md`：任务目标、动态计划、进度和最小恢复上下文；
- `project_result_index.md`：跨任务 / 跨对话的正式结果检索入口，不保存当前任务状态。

任务级状态：

```text
未完成
已完成
已终止
```

普通子环节状态：

```text
待执行
未完成
已完成
```

Stage-specific 内部对象如有不同状态模型，以对应 current Stage Skill 为准。

## Runtime entry and current Skill loading

Task Execution Agent 持续执行一个 Task Sheet。

进入或恢复任务时：

1. 读取目标 `tasks/Txxxx.md`；
2. 确定当前需要处理的 Stage / Step / Stage-specific plan item；
3. 如果该 Stage 存在负责 stage-wide runtime / orchestration 的 current Stage main Skill，按当前任务需要读取；
4. 读取当前具体 Step / capability 的 current main Skill；
5. 只按当前对象需要继续读取 reference、supporting Skill、Tool guide 或实际科研文件。

如果计划中的 Stage / Step 只有 architecture freeze、尚无获批生成的 current runtime Skill，不得把 freeze 当作执行指南自行运行。

## Task execution loop

普通执行主线：

```text
读取目标 Task Sheet
→ 确定当前任务项 / 对象
→ 读取需要的 current Stage / Step Skill
→ 按当前 Skill / Stage 规则判断 reuse
→ 按需读取实际对象、候选结果、reference / supporting Skill / Tool guide
→ 需要时执行
→ 按结果 owner 的规则 validation
→ 更新 Task Sheet 当前项
→ 登记正式结果
→ 根据实际结果或用户要求维护尚未完成的后续计划
→ 继续下一任务项
```

这里的“维护尚未完成的后续计划”只规定**必须能够更新计划**这一通用 runtime 机制，不替代 Stage-specific 的科学调整规则。

例如某个结果是否意味着后续 Step 应删除、增加、重排、重新进入，或某类 failure 应回到哪个上游 owner，如果对应 Stage 已有 main Skill 定义这些关系，则遵循该 Stage main Skill；本 Skill 不创建第二套科学决策规则。

普通子环节之间不返回 Manager 调度。只有用户明确要求 Manager 重新规划时，才重新进入 Manager 的 explicit replanning 职责。

## Manager boundary

Manager current entry：

`00_manager/SKILL.md`

Manager 负责：

- 定位 / 创建任务；
- 生成初始 Task Sheet；
- 用户明确要求时重新规划；
- 项目级任务导航 / 整理。

Manager 不执行具体科研 Step，也不替 Task Execution runtime 判断具体 Step 的 reuse、scientific applicability 或 runtime validation。

## Directory model

普通 Step 的 task-specific 工作目录采用：

```text
<base_work_directory>/<task_id>/
```

Manager 可以在 Task Sheet 中记录未来路径，但不提前创建 task-specific directory。

真正进入当前工作时：

```text
先检查 reuse
├─ 可直接复用 → 不创建无用空目录
└─ 需要本地执行 → 创建当前 task-specific directory
```

Stage-specific directory / index 组织以对应 current Stage Skill 为准。

## Reuse

普通工作在真正开始时判断 reuse：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前用户可见 Agent 向用户确认
用户明确要求重做 / 对照 → 跳过自动复用
```

不得仅根据目录存在、文件名相同或任务名称相似自动复用。

跨任务复用已有正式结果时直接引用原结果，不为了当前任务复制无意义副本。

若某 Stage current Skill 定义了不同的 reuse 组织方式，以该 Stage current Skill 为准。

## Validation and results

Validation 默认跟随当前结果 owner：

```text
谁产生 / 判定结果
→ 谁拥有该结果的 validation requirement
```

Tool 可以负责自己确定性输出的机械 / 格式有效性；科研 main Skill 仍负责判断该输出是否满足当前科研目标。

`project_result_index.md` 只登记当前 Skill / Stage 定义的正式结果或结果事项，不登记 debug、scratch、cache 或为了“完整”而产生的重复文件索引。

## Minimal reads

真实科研 runtime 按需读取。

Task Execution 不默认：

- 预读全部未来 Steps；
- 扫描所有任务；
- 重读上游全过程；
- 加载 Legacy route / state / event / runtime records；
- 为了寻找潜在 reuse 而无边界遍历项目。

需要理解当前接口时，可以读取直接相关的外部 Skill；读取不改变其内容 owner。

## Stage-specific boundary

职责关系固定为：

```text
00_runtime/SKILL.md
→ 跨 Stage 通用 Task Execution 机制

Stage main Skill（存在且确有 Stage-wide 职责时）
→ Stage-specific orchestration / plan adjustment / shared Stage objects

Step / capability Skill
→ 具体科研处理、判断、validation 与 results
```

不得因为本 Skill定义了“可以动态维护 Task Sheet”，就把某个 Stage 内“如何根据科研结果调整计划”的规则上移到这里。

## Legacy rule

Legacy Runtime 可以保留用于 Git history、旧项目迁移、明确调试或历史审计，但：

- 新项目不默认生成 Legacy records；
- current runtime 不双写旧 records；
- 新 Skill 不为普通运行增加 Legacy compatibility layer；
- archived / Legacy 文件不能推翻 current Skill 或本 runtime Skill。
