# MD Workflow Skills

用于设计和维护基于 Skill 的分子动力学工作流。

## 当前运行架构

- 主智能体加载 Manager Skill，维护项目级状态并统一与用户交互。
- Workflow Skill 定义可复用的阶段流程，不作为独立 Agent 运行。
- Workstream 表示真实项目中的一条具体工作分支，可以依次经过多个 Workflow。
- Manager 串行创建临时子 Agent，执行局部 Operation、Validator，或二者组成的上下文连续任务单元。
- 任意时刻最多存在一个前台临时子 Agent，但允许多个 Workstream 和多个 tmux/调度任务并存。
- 子 Agent 用于隔离文件内容、命令输出、日志和中间分析，减少主智能体上下文污染。

## 当前 Workflow 划分

1. `structure_preparation`
2. `topology_preparation`
3. `md_preparation`
4. `md_simulation`
5. `analysis`

职责边界：

- `structure_preparation`：初始结构识别、对象选择、缺失处理、质子化、重排与结构验证。
- `topology_preparation`：标准残基、相连非标准残基和独立非标准组分的拓扑生成与参数准备。
- `md_preparation`：力场与拓扑整合、建盒、加水、加离子，并生成完整可用于模拟的体系。
- `md_simulation`：准备对应阶段的 MDP 与运行输入，执行 EM、NVT、NPT、生产 MD、续跑及完成状态核验。
- `analysis`：模拟结果分析。

## Workstream 项目模型

项目不保存唯一的“当前 Workflow”。同一项目可同时存在多个 Workstream，例如：

- 参数 v1 的生产 MD 正在后台运行；
- 参数 v2 返回 `topology_preparation` 重新生成参数并执行测试 MD；
- 对照体系等待人工决策。

每个 Workstream 独立保存目标、当前位置、预计路线、产物谱系、人工决策和外部运行任务。当前一轮 Manager 交互通过 `focus` 指定主要处理对象，其他 Workstream 可以作为关联上下文或继续后台运行。

## 真实 MD 项目的建议顶层目录

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

状态目录建议结构：

```text
00_project_state/
├── project_state.yaml
├── project_state.yaml.bak
└── workstreams/
    └── <workstream_id>.yaml
```

记录目录建议结构：

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

- `00_project_state/` 只保存当前有效且可恢复的项目索引与 Workstream 状态。
- `00_project_records/` 保存 Manager、项目事件、路线、任务、人工决策、作业提交和状态快照等历史记录。
- Manager 的历史记录放在 `00_project_records/manager/`。
- `04_md_simulation/` 的内部目录不在项目级预先排序或固定，由对应 Workflow 和 Skill 根据实际任务定义。

详细已确认决策见 `design_records/manager_and_project_structure_decisions.md`。
