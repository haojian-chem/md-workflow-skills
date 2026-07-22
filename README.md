# MD Workflow Skills

用于设计和维护基于 Skill 的分子动力学工作流。

## 当前运行架构

- 主智能体加载 Manager Skill，维护项目级状态并统一与用户交互。
- Workflow Skill 负责生成和动态调整预计路线，不作为独立 Agent 运行。
- Manager 串行创建临时子 Agent，执行局部 Operation、Validator，或二者组成的上下文连续任务单元。
- 子 Agent 的主要目的为隔离文件内容、命令输出、日志和中间分析，减少主智能体上下文污染。
- 当前 MD 流程不并行执行。

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

- `00_project_state/` 保存整个项目当前有效且可恢复的状态，不保存历史堆积。
- `00_project_records/` 保存 Manager、Workflow、任务、人工决策、路线变化和作业提交等历史记录。
- Manager 的历史记录放在 `00_project_records/manager/`，不放入状态目录。
- `04_md_simulation/` 的内部目录不在项目级预先排序或固定，由对应 Workflow 和 Skill 根据实际任务定义。

详细已确认决策见 `design_records/manager_and_project_structure_decisions.md`。
