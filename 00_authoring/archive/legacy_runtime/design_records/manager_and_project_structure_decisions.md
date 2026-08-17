# Manager 与项目状态设计决策记录

## 1. 顶层 Workflow

当前采用：

```text
structure_preparation
→ topology_preparation
→ md_preparation
→ md_simulation
→ analysis
```

不单独设置 `system_preparation`。

## 2. 各 Workflow 的职责边界

### structure_preparation

负责：

- 初始结构来源识别；
- 组分与残基分类；
- 链和组分选择；
- altloc/occupancy 处理；
- 缺失区域识别与补全；
- 蛋白质子化；
- 结构重排、映射和最终结构验证。

### topology_preparation

只负责拓扑生成与参数准备：

- 标准残基拓扑；
- 相连非标准残基拓扑与参数；
- 独立非标准组分拓扑与参数；
- 上述对象所需的原子类型、成键项、电荷和参数文件准备。

本 Workflow 不负责建盒、加水或加离子。

### md_preparation

负责完整模拟体系的构建：

- 力场和拓扑整合；
- 分子与拓扑顺序整合；
- 建盒；
- 加水；
- 中和与目标盐浓度加离子；
- 生成并验证完整体系。

本 Workflow 不负责 MDP 文件和实际模拟运行。

### md_simulation

负责模拟输入和实际 MD 运行：

- EM、NVT、NPT、生产 MD 等阶段的 MDP 准备；
- 生成各阶段运行输入；
- 执行或提交 EM、NVT、NPT 和生产 MD；
- 使用 tmux 或调度系统管理长耗时任务；
- 续跑；
- 运行状态和完成状态核验。

### analysis

负责模拟输出的分析流程。具体范围后续单独设计。

## 3. Workflow 与 Workstream

Workflow 是可复用的阶段流程定义。Workstream 是真实项目中的一条具体工作分支，可以依次经过多个 Workflow。

项目不再保存唯一的“当前 Workflow”。同一项目可以同时存在多个 Workstream，例如：

- `ws_main_v1`：使用参数 v1 的生产 MD 正在后台运行；
- `ws_parameter_v2`：返回 `topology_preparation` 生成参数 v2，并继续执行测试 MD；
- `ws_control`：对照体系等待人工决策。

运行约束：

- 任意时刻最多一个前台临时子 Agent；
- 可以同时存在多个 Workstream；
- 可以同时存在多个 tmux 或调度系统外部任务；
- 后台运行不会自动成为当前 Focus；
- Manager 不高频轮询外部任务。

### 创建新 Workstream 的条件

满足任一情况时，应从指定产物节点创建新 Workstream，而不是把整个项目阶段回退：

- 已生成依赖旧结果的有效下游产物；
- 已经开始 EM、NVT、NPT 或生产 MD；
- 需要保留旧参数或旧体系；
- 需要比较不同参数、方案、重复或对照；
- 上游修改可能使现有下游结果失效；
- 用户明确要求新版本或测试分支。

如果当前步骤尚未闭合、没有有效下游依赖且修改不会使其他结果失效，可以在原 Workstream 内修正后重新验证。

## 4. 项目顶层目录

```text
<project_root>/
├── 00_project_state/
├── 00_project_records/
├── 01_structure_preparation/
├── 02_topology_preparation/
├── 03_md_preparation/
├── 04_md_simulation/
└── 05_analysis/
```

目录名采用 `project`，因为状态和记录服务于整个 MD 项目，不只描述 Workflow 调度。

`04_md_simulation/` 的内部目录不在项目级预设编号或固定结构。不同项目可能包含多体系、多重复、分支、续跑、umbrella sampling、metadynamics 或 PMF 等不同组织方式，具体结构由对应 Workflow 和局部 Skill 决定。

## 5. 当前状态与历史记录分离

### 00_project_state

```text
00_project_state/
├── project_state.yaml
├── project_state.yaml.bak
└── workstreams/
    └── <workstream_id>.yaml
```

`project_state.yaml` 是项目级权威入口，只保存：

- Project root 与 Skill root；
- 项目入口状态；
- Workstream 索引；
- 当前 Focus；
- 项目级待处理决策；
- 项目级最后事件引用。

每个 `workstreams/<workstream_id>.yaml` 是该 Workstream 当前状态的权威文件，保存：

- Workstream 标识、标题和目标；
- 父 Workstream 与分支来源；
- 当前 Workflow 与任务位置；
- 生命周期状态、活动状态和暂停原因；
- 当前路线引用；
- 结构、拓扑、完整体系等产物谱系引用；
- 当前人工决策和外部任务。

状态目录不保存完整历史。状态更新采用临时文件、解析检查、备份和原子替换。

### 00_project_records

```text
00_project_records/
├── manager/
├── events/
├── workstreams/
│   └── <workstream_id>/
│       ├── routes/
│       ├── tasks/
│       ├── decisions/
│       └── submissions/
└── state_snapshots/
```

其中：

- `manager/` 保存 Manager 级人类可读历史；
- `events/` 保存项目级机器可读事件流水；
- `workstreams/<id>/routes/` 保存该分支的预计路线及修订；
- `workstreams/<id>/tasks/` 保存临时子 Agent 任务包、结果和摘要；
- `workstreams/<id>/decisions/` 保存人工决策历史；
- `workstreams/<id>/submissions/` 保存 tmux 或调度作业提交记录；
- `state_snapshots/` 只在关键节点保存项目或 Workstream 状态快照。

## 6. 用户请求动作

用户请求通常同时包含检查、规划和执行，因此不采用互斥启动模式。

```yaml
requested_actions:
  - INSPECT
  - PLAN
  - EXECUTE
```

三类动作可以任意组合：

- `INSPECT`：读取和核验当前状态、产物或运行任务；
- `PLAN`：生成或调整指定 Workstream 的预计路线；
- `EXECUTE`：在明确范围和停止条件下推进任务。

每次 Manager 进入项目都执行最小状态检查，但完整检查范围由用户请求决定。

## 7. 项目入口状态

项目入口状态只回答：Manager 是否能够安全解释并继续管理整个项目。

```yaml
entry_state: NEW | RESUMABLE | NEEDS_RECOVERY
```

### NEW

适用条件：

- 不存在可读取的项目状态；
- 项目目录为空或只有初始输入；
- 没有明显的旧结构、拓扑、完整体系或模拟结果。

Manager 可以确认两个根目录、创建管理目录、建立首个 Workstream 并生成路线。

如果没有状态文件但已存在大量业务产物，不得判为 `NEW`，应进入恢复。

### RESUMABLE

适用条件：

- 项目级状态可解析并符合 schema；
- 两个根目录有效；
- 登记的 Workstream 状态文件可定位；
- 项目索引、路线、关键产物和任务记录之间没有项目级阻断性矛盾；
- Manager 能识别本轮请求的目标范围。

`RESUMABLE` 项目可以同时包含：

- 后台运行的 Workstream；
- 等待人工决策的 Workstream；
- 失败或暂停的 Workstream；
- 需要局部恢复的非目标 Workstream；
- 已完成或归档的 Workstream。

只要局部异常已被明确记录、不会污染其他分支且不阻止当前目标安全执行，项目整体仍可保持 `RESUMABLE`。

### NEEDS_RECOVERY

适用条件包括：

- `project_state.yaml` 损坏、不可解析或 schema 不兼容；
- Workstream 索引与实际文件严重冲突；
- Project root 或 Skill root 无法确定；
- 当前目标 Workstream 无法安全解释；
- 多个 Workstream 意外写入同一应隔离目录；
- 参数、体系或产物版本引用发生冲突；
- 外部任务状态与 tmux/调度系统事实无法对应；
- 旧项目已有大量产物但没有可信状态记录。

项目级恢复完成前，不创建新的写入任务。

## 8. 项目级与 Workstream 级恢复

### 项目级恢复

```yaml
entry_state: NEEDS_RECOVERY
recovery_scope: PROJECT
```

用于项目索引、根目录、Workstream 清单或公共文件所有权不可信的情况。项目索引恢复前，全部新写入暂停。

### Workstream 级恢复

项目整体可以保持：

```yaml
entry_state: RESUMABLE
```

问题分支记录：

```yaml
activity_status: NEEDS_RECOVERY
```

其他不依赖该分支的 Workstream 可以继续运行或执行。只有当前目标、共享依赖或文件冲突受影响时，才升级为项目级恢复。

## 9. Workstream 状态

Workstream 状态拆成三个维度。

### 生命周期状态

```yaml
lifecycle_status: OPEN | COMPLETED | ARCHIVED | ABANDONED
```

- `OPEN`：仍可能继续规划或执行；
- `COMPLETED`：已达到该 Workstream 的目标终点；
- `ARCHIVED`：保留记录但默认不再作为活动分支展示；
- `ABANDONED`：明确终止并保留原因和历史。

### 活动状态

```yaml
activity_status: IDLE | READY | EXECUTING | RUNNING_EXTERNAL | WAITING | FAILED | NEEDS_RECOVERY
```

- `IDLE`：当前没有已确定的下一任务；
- `READY`：下一任务已确定并可执行；
- `EXECUTING`：当前存在前台临时子 Agent；
- `RUNNING_EXTERNAL`：存在 tmux 或调度系统中的外部任务；
- `WAITING`：因人工决定、输入、依赖或资源而暂停；
- `FAILED`：当前任务明确失败且尚未决定后续；
- `NEEDS_RECOVERY`：该分支状态或产物谱系无法安全解释。

同一时刻最多一个 Workstream 为 `EXECUTING`，但可以有多个 Workstream 为 `RUNNING_EXTERNAL`。

### 暂停原因

```yaml
hold_reason:
  type: NONE | USER_DECISION | MISSING_INPUT | DEPENDENCY | USER_PAUSED | EXTERNAL_RESOURCE
```

`hold_reason` 主要用于解释 `WAITING`，不得替代任务失败或恢复状态。

## 10. Focus

Focus 表示当前一轮 Manager 交互的主要规划、执行或恢复对象，不表示项目唯一活动分支。

```yaml
focus:
  target_type: PROJECT | WORKSTREAM
  workstream_id: ws_0002_param_v2_test
  reason: USER_SELECTED | EXECUTION_TARGET | RECOVERY_TARGET | LAST_ACTIVE
  selected_at: 2026-07-22T15:00:00+08:00
```

- `target_type: PROJECT`：用于项目级检查、索引恢复、全局规划或多个分支汇总；
- `target_type: WORKSTREAM`：用于某一具体分支的规划、执行或恢复。

一个 Workstream 至少包含：

```yaml
workstream_id: ws_0002_param_v2_test
title: 参数 v2 测试
purpose: 使用参数集 v2 构建新体系并完成短时测试 MD
```

- `workstream_id` 是稳定机器标识，创建后不随标题修改；
- `title` 是用户可读短名称；
- `purpose` 说明该分支的目标和与其他分支的区别。

本轮还可以记录关联分支：

```yaml
related_workstreams:
  - workstream_id: ws_0001_main_v1
    relation: INSPECTION_CONTEXT
```

一个 Manager 运行周期只有一个主要 Focus，但可以读取多个关联 Workstream。

Focus 选择优先级：

1. 用户明确指定的 Workstream；
2. 用户指定任务或产物所属的 Workstream；
3. 本轮需要实际写入或执行的 Workstream；
4. 当前存在未完成前台任务的 Workstream；
5. 最近一次 Focus；
6. 仍无法唯一判断时向用户确认。

后台 MD 正在运行本身不会自动改变 Focus。

### 用户界面展示

```text
Focus workstream:
参数 v2 测试 [ws_0002_param_v2_test]

目标：
使用参数集 v2 构建新体系并完成短时测试 MD。

当前位置：
topology_preparation / connected_nonstandard_topology

本轮范围：
从 connected_nonstandard_topology
到 md_simulation / test_nvt

本轮动作：
INSPECT + PLAN + EXECUTE
```

项目进入时还应展示：

- Skill root；
- Project root；
- 当前 Focus；
- Focus 的当前阶段与预计下一任务；
- Focus 的当前人工决策；
- 后台运行任务；
- 其他活动 Workstream 摘要。

完整预计路线只在首次生成或发生实际变化时展示。

## 11. 预计路线

预计路线属于 Workstream，而不是整个项目的唯一全局路线。

路线可以：

- 只包含一个局部环节；
- 从某个 Workflow 的中间步骤开始；
- 跨越多个 Workflow；
- 在用户指定的中间步骤结束。

路线不是硬性锁定的执行清单。执行结果、人工决策、验证结果或已有文件状态变化时，Manager 可以创建新的路线修订。旧路线保留在对应 Workstream 的记录目录中，当前状态只引用有效路线 ID。
