# Manager 与项目目录设计决策记录

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

## 3. 项目顶层目录

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

目录名采用 `project` 而不是 `workflow`，因为状态和记录服务于整个 MD 项目，不只描述 Workflow 调度。

## 4. 当前状态与历史记录分离

### 00_project_state

只保存整个项目当前有效、可恢复的状态，例如：

- Skill 根目录与项目根目录；
- 当前 Workflow 和当前任务；
- 当前预计路线；
- 当前有效输入和输出；
- 待处理人工决策；
- 已提交但尚未结束的运行任务状态。

该目录不保存完整历史。

建议使用单数 `state`，表示一个项目状态存储区；不使用 `states`。

### 00_project_records

保存历史和审计记录，例如：

```text
00_project_records/
├── manager/
├── workflows/
├── tasks/
├── decisions/
├── routes/
└── submissions/
```

其中：

- `manager/` 保存 Manager 级历史记录；
- `workflows/` 保存各 Workflow 的决策历史；
- `tasks/` 保存临时子 Agent 任务记录；
- `decisions/` 保存人工决策历史；
- `routes/` 保存预计路线及其变化；
- `submissions/` 保存 tmux 或调度作业提交记录。

具体日志文件格式、轮转、备份和保留策略后续单独设计。

## 5. md_simulation 内部目录

不在项目级预设编号子目录。

原因：

- 实际模拟可能包含多个体系、重复、分支和续跑；
- 不同项目的 EM、NVT、NPT 和生产 MD 组合可能不同；
- umbrella sampling、metadynamics、PMF 等任务会产生不同组织方式；
- 子目录结构应由 `md_simulation_workflow` 及其局部 Skill 根据实际任务定义。

## 6. 预计路线

Manager 在首次进入项目或用户指定执行范围时生成预计路线。路线可以：

- 只包含一个局部环节；
- 从某个 Workflow 的中间步骤开始；
- 跨越多个 Workflow；
- 在用户指定的中间步骤结束。

预计路线不是硬性锁定的执行清单。执行结果、人工决策、验证结果或已有文件状态发生变化时，Manager 可以重新计算路线；只有首次生成或路线实际变化时才向用户完整展示。
