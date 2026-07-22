# MD Workflow Skills

用于设计和维护基于 Skill 的分子动力学工作流。

## 当前运行架构

- 主智能体加载 Manager Skill，维护全局状态并统一与用户交互。
- Workflow Skill 负责生成和动态调整预计路线，不作为独立 Agent 运行。
- Manager 串行创建临时子 Agent，执行局部 Operation、Validator 或二者组成的上下文连续任务单元。
- 子 Agent 的主要目的为隔离文件内容、命令输出、日志和中间分析，减少主智能体上下文污染。
- 当前 MD 流程不并行执行。

## 当前 Workflow 划分

1. `structure_preparation`
2. `topology_preparation`
3. `md_preparation`
4. `md_simulation`
5. `analysis`

其中：

- `topology_preparation` 包含建盒、溶剂化和加离子等体系构建工作。
- `md_preparation` 将已验证的体系转换为可运行的 EM、NVT、NPT 和生产 MD 任务，包括参数、输入、依赖关系与运行脚本准备，但不执行长耗时模拟。
- `md_simulation` 只负责实际运行 EM、NVT、NPT、生产 MD 及其续跑和完成核验。

## 真实 MD 项目的建议顶层目录

```text
<project_root>/
├── 00_workflow_state/
├── 00_workflow_records/
├── 01_structure_preparation/
├── 02_topology_preparation/
├── 03_md_preparation/
├── 04_md_simulation/
└── 05_analysis/
```

`04_md_simulation/` 的内部目录不在项目级预先排序或固定，由对应 Workflow 和 Skill 根据实际任务定义。

详细已确认决策见 `design_records/manager_and_project_structure_decisions.md`。
