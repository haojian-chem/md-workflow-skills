# Lightweight Runtime v2 Specification

Status: CURRENT DEFAULT RUNTIME ARCHITECTURE

本文件只定义**跨 Stage 的通用运行架构**。具体科研规则、Stage-specific execution objects、字段和文件生命周期由对应 current Stage Skill 或 current architecture freeze 拥有；architecture freeze 可以是 current authoring authority，但不因此成为可执行 runtime Skill。

## 1. Goal

默认运行方式：

```text
Manager
→ Task Sheet
→ long-lived Task Execution Agent
→ current main Skill
→ 按需读取 references / supporting Skills / Tool guides
```

目标是让 Agent 直接依据当前科研 Skill 推进任务，而不是把普通科研执行包装成事务型 workflow engine。

默认不依赖：

```text
Workstream
route / route revision
runtime task/result
project event
artifact state machine
transaction closure
runtime projection state
```

## 2. Project records

默认项目记录：

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
- `project_result_index.md`：跨任务/跨对话的正式结果检索入口，不保存当前任务状态。

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

Stage-specific 内部对象如有不同状态模型，以对应 Stage current Skill / freeze 为准。

## 3. Manager boundary

Manager 与 Task Execution Agent 默认是不同对话。

Manager 负责：

1. 定位已有任务；
2. 创建新任务；
3. 生成初始 Task Sheet 计划；
4. 用户明确要求时重新规划；
5. 项目级任务导航/整理。

Manager 默认不：

- 执行具体科研 Step；
- 判断具体 Step 的 reuse / applicability；
- 预读全部科研 Skills；
- 为普通任务建立 route / event / Workstream；
- 提前创建 task-specific 科研执行目录。

Manager 初始规划规则由：

`00_manager/SKILL.md`

及其 planning reference 拥有。

## 4. Task Execution Agent

Task Execution Agent 长期持有一个 Task Sheet，并连续推进任务。

普通执行主线：

```text
读取目标 Task Sheet
→ 确定当前任务项 / 对象
→ 读取当前 main Skill
→ 按当前 Skill / Stage 规则判断 reuse
→ 按需读取实际对象、候选结果、reference / supporting Skill / Tool guide
→ 需要时执行
→ 按结果 owner 的规则 validation
→ 更新 Task Sheet
→ 登记正式结果
→ 根据实际结果或用户要求调整尚未完成的后续计划
→ 继续下一任务项
```

普通子环节之间不返回 Manager 调度。

如果某个已规划 Stage / Step 只有 architecture freeze、尚无获批生成的 current runtime Skill，则 Task Execution Agent 不得把 freeze 当作执行指南自行运行该 Stage / Step；应等待对应 Skill authoring / generation 完成。

## 5. Directory model

普通 Step 的 task-specific 工作目录采用：

```text
<base_work_directory>/<task_id>/
```

项目初始化可以创建稳定 Step base directories。

Manager 可以在 Task Sheet 中记录未来路径，但不提前创建 task-specific directory。

Task Execution Agent 真正进入该工作时：

```text
先检查 reuse
├─ 可直接复用 → 不创建无用空目录
└─ 需要本地执行 → 创建当前 task-specific directory
```

Stage-specific directory/index 组织以对应 Stage current Skill / freeze 为准。

## 6. Reuse

普通工作在真正开始时判断 reuse：

```text
明确等价 → 自动复用
明确不等价 → 正常执行
信息不足 → 当前用户可见 Agent 向用户确认
用户明确要求重做/对照 → 跳过自动复用
```

不得仅根据目录存在、文件名相同或任务名称相似自动复用。

跨任务复用已有正式结果时直接引用原结果，不为了当前任务复制一份无意义副本。

若某 Stage 已冻结不同的 reuse 组织方式，以该 Stage current Skill / freeze 为准。

## 7. Validation and results

Validation 默认由当前结果 owner 定义。

```text
谁产生 / 判定结果
→ 谁拥有该结果的 validation requirement
```

Tool 可以负责自己确定性输出的机械/格式有效性；科研 main Skill 仍负责判断该输出是否满足当前科研目标。

`project_result_index.md` 只登记当前 Skill / Stage 定义的正式结果或结果事项，不登记 debug、scratch、cache 或为了“完整”而产生的重复文件索引。

## 8. Minimal reads

真实科研 runtime 按需读取。

Manager 不默认读取：

- `project_result_index.md`；
- 无关 Task Sheets；
- 全部科研 Skills；
- Legacy runtime records。

Task Execution Agent 不默认：

- 预读未来 Steps；
- 扫描所有任务；
- 重读上游全过程；
- 加载 Legacy route/state/event/runtime records。

需要理解当前接口时，可以读取直接相关的外部 Skill；读取不改变其内容 owner。

## 9. Stage-specific exceptions

跨 Stage runtime 只在这里承认“存在例外”，不复制例外内部 schema。

Stage 4 current runtime authority：

```text
04_md_simulation/SKILL.md
```

Stage 4 architecture authority：

```text
00_authoring/architecture_freezes/WORKFLOW4_STAGE4_ARCHITECTURE_FREEZE.md
```

Stage 5 当前尚无 active runtime Skill。其 current architecture authority 为：

```text
00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md
```

未来只有在用户明确批准 Stage 5 Skill generation 并正式生成后，以下路径才可成为 Stage 5 runtime authority：

```text
05_analysis/SKILL.md
```

因此，Stage 4 run-unit 的具体字段、reuse 和生命周期由 current Stage 4 Skill 定义；Stage 5 plan items / prepared-input indexes 等已冻结设计目前只作为后续 Skill generation 的 authoring input，不得在 runtime 中把 architecture freeze 当作可执行 Stage 5 Skill。

## 10. Legacy rule

Legacy Runtime 可以保留用于 Git history、旧项目迁移、明确调试或历史审计，但：

- 新项目不默认生成 Legacy records；
- Lightweight Runtime 不双写旧 records；
- 新 Skill 不为普通运行增加 Legacy compatibility layer；
- archived / Legacy 文件不能推翻 current Skill、current Stage freeze 或本 runtime specification。
