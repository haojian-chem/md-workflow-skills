# Manager 与项目目录设计决策记录

## 1. 顶层 Workflow

当前采用：

```
structure_preparation
→ topology_preparation
→ md_preparation
→ md_simulation
→ analysis
```

不单独设置 `system_preparation`。

原因：

- structure_preparation 与 topology_preparation 共同完成体系建立；
- topology_preparation 已包含建盒、溶剂化、加离子等步骤；
- 避免 system preparation 与具体 Workflow 重复。

## 2. 项目目录

```
<project_root>/
├── 00_workflow_state/
├── 00_workflow_records/
├── 01_structure_preparation/
├── 02_topology_preparation/
├── 03_md_preparation/
├── 04_md_simulation/
└── 05_analysis/
```

## 3. 状态与记录分离

### workflow_state

保存当前有效状态：

- 当前阶段；
- 当前任务；
- 当前预计路线；
- 待确认事项。

### workflow_records

保存历史信息：

- Manager 运行记录；
- 任务历史；
- 路线变化；
- 状态变化。

日志格式和详细结构后续单独设计。

## 4. md_preparation 与 md_simulation

md_preparation：

- 负责模拟任务准备；
- 输入检查；
- 参数配置；
- 生成运行所需文件；
- 不负责实际长时间运行。

md_simulation：

- 负责 EM；
- NVT；
- NPT；
- production MD；
- 续跑；
- 运行状态核验。

## 5. md_simulation 内部目录

不预设统一编号目录。

原因：

- 实际模拟流程可能存在分支；
- 不同项目可能执行不同组合；
- 子目录定义由对应 Skill 设计。

