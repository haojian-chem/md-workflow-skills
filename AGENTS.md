# MD Workflow Skill Project Instructions

## 1. 项目范围

本仓库用于设计、实现、审查和维护分子动力学工作流 Skills。

Skill 架构根目录：

`/root/data/5_codex/3_md_workflow`

真实 MD 项目根目录不固定。运行 Manager 时必须分别确认或读取 Skill 架构根目录与真实 MD 项目根目录。

## 2. 运行时模型

- Workflow 是可复用阶段 Skill，不是 Agent；
- Workflow 规划时返回本阶段 route fragment，执行时返回一个当前 decision；
- Workstream 是真实项目中的具体工作分支，一个 Workstream 可以经过多个 Workflow；
- 一个项目可以同时存在多个 Workstream；
- Manager 负责跨 Workflow 起终点、fragment 拼接、route revision、状态和记录；
- 主智能体执行时只加载 Manager 与当前 Workflow；
- Manager 每次最多创建一个前台临时子 Agent；
- 临时子 Agent 执行一个 task unit：`OPERATION`、`VALIDATOR` 或 `OPERATION_WITH_VALIDATOR`；
- Operation 与专属 Validator 即使同一子 Agent 连续执行，也必须分开记录结果；
- 子 Agent 用于上下文隔离，不用于前台并行；
- 多个 tmux 或调度系统外部任务可以并存，但 Manager 不高频轮询；
- 子 Agent 不得继续委派，也不直接与用户交互。

## 3. Skill 开发与运行必须分开

### 路线规划

```text
Manager
→ 按 stage registry 逐个读取涉及的 Workflow
→ workflow route fragments
→ Manager 核验 artifact 接口并拼接 Workstream route
```

### MD 执行

```text
主智能体
├── Manager Skill
├── 当前 Workflow Skill
└── 最多一个前台临时子 Agent
    ├── Operation
    ├── Validator
    └── 或 Operation → 专属 Validator
```

### Skill 开发

- 用户可以在网页端打开多个独立窗口；
- 每个窗口只编写被分配的 Skill 或互斥文件范围；
- 网页窗口不是运行时 Agent；
- 项目中不得为编写窗口创建开发子 Agent 角色或配置。

## 4. 权威文件

跨 Skill 的状态、Focus、Workflow route fragment、Workflow decision、task unit、子 Agent 返回、项目与 Workstream 状态、事件、路线、决策、submission、artifact set 和 snapshot 只由：

`03_contracts/`

定义。入口索引为：

`03_contracts/README.md`

跨 Workflow 路线规划规则只由：

`00_manager/md_workflow_manager/references/route_planning_protocol.md`

定义。

四层职责、运行时子 Agent 协议、内容归属和多窗口编写规则只由：

`00_authoring/md-workflow-skill-authoring/references/`

定义。

具体 Skill 只能引用，不得复制并重新定义。

## 5. 四层关系

```text
规划：
Manager → Workflow route fragments → Workstream route

执行：
Manager → current Workflow decision → task unit → Operation / Validator
```

- Manager 负责 requested actions、项目入口状态、Focus、Workstream、跨 Workflow 路线、用户交互、状态和记录提交；
- Workflow 负责本阶段 substep、route fragment、当前下一任务、条件、跳过、gate 和完成判断；
- Operation 负责具体文件或命令操作；
- Validator 负责检查与结构化判定。

Workflow 不执行 Operation/Validator，不创建子 Agent，不选择项目 Focus，不创建 Workstream，也不拼接其他 Workflow。

Manager 不得根据阶段名称自行编造 Workflow 内部步骤，也不得脱离 execution decision 自行选择局部业务步骤。

## 6. 路线规划规则

- 每个 Workflow 只生成自身阶段的 `workflow_route_fragment`；
- Manager 解析起点、终点和停止条件；
- Manager 按 stage registry 逐个请求 fragment；
- 相邻 fragment 的 exit artifact 必须满足下一 fragment 的 entry requirement；
- 条件步骤标记 `REQUIRED | CONDITIONAL`；
- 无证据时不得提前删除条件步骤；
- 未连接 Workflow 在边界形成 `PARTIAL | BLOCKED`，不得虚构内部步骤；
- route record 创建后不可覆盖，修订通过新 route 和 `supersedes` 表达；
- execution decision 因新证据与 active route 不一致时，必须先修订路线或暂停；
- 预计路线是动态投影，不是硬编码批处理队列。

## 7. 项目状态与记录权限

Manager 是以下目录的唯一提交者：

```text
00_project_state/**
00_project_records/**
```

Operation 和 Validator：

- 只能在 task unit 授权的业务路径写入；
- 不得修改项目状态或结构化历史记录；
- 只返回候选 artifact、决策请求和详细业务日志路径，由 Manager 持久化。

外部任务从 `RUNNING` 结束后必须先进入 `FINISHED_UNVERIFIED`，完成输出核验后才能标记为 `COMPLETED` 或 `FAILED`。

## 8. 修改前回顾

提出或实施新方案前，先列出：

```text
已做过
已否定
仍未验证
```

若新方案与已失败方案重复或本质等价，且没有新证据改变前提，不得再次执行。

## 9. 内容唯一归属

一条规则只能有一个权威位置：

- 项目通用规则：`AGENTS.md` 或 authoring references；
- 跨 Skill 接口：`03_contracts/`；
- 跨 Workflow 路线拼接：Manager route planning protocol；
- 阶段内路线片段和执行逻辑：对应 Workflow `SKILL.md`；
- 当前 Operation/Validator 的执行逻辑：当前 `SKILL.md`；
- 当前 Skill 独有领域数据：当前 `references/`；
- 当前 Skill 独有输出结构：当前 `schemas/`；
- 示例与评测夹具：`04_evals/<skill-name>/fixtures/`。

其他文件只引用，不复述完整定义。

## 10. 多窗口文件所有权

- 新窗口开始前读取 `00_authoring/SYNC_STATUS.md`、`skill_inventory.yaml`、`file_ownership.yaml`、目标 content map、work order 和适用 contracts；
- 涉及 Workflow 或路线时读取 route planning protocol；
- 同一文件同一时间只有一个编写窗口；
- 一个 Skill 目录默认只有一个编写窗口；
- `AGENTS.md`、`03_contracts/`、authoring references、Manager references、design records、content maps、inventory 和 ownership 表只由主窗口修改；
- 写入路径重叠时不得同时编写；
- 共享 contract 的变更由业务窗口提交请求，主窗口统一裁决；
- 网页窗口之间不通过开发子 Agent 配置协调。

## 11. Workstream 分支规则

已生成有效下游产物、已启动 EM/NVT/NPT/MD、需要保留旧参数或需要比较方案时，不得把项目唯一阶段“回退”并覆盖旧结果。

应从明确的 artifact 节点创建新 Workstream。

只有当前步骤尚未闭合、没有有效下游依赖且修改不会影响其他结果时，才允许在原 Workstream 内修正。

## 12. 权限与安全

- 不修改 `01_sources/` 中的来源文件；
- source recognition 默认复制源结构并校验 SHA-256；只有明确用户授权和 source write permission 同时存在时才允许移动；
- 不自动通过单位计费的期刊数据库下载文献；
- 未经授权，不删除、覆盖或批量移动项目文件；
- 破坏性或不可逆操作由 Manager 汇总后请求用户确认；
- Workflow、Operation、Validator 和临时子 Agent 均不直接向用户请求确认。

## 13. 完成定义

Skill 只有在以下条件全部满足时才可通过：

- 层级与局部 contract 已确认；
- content map 已确认；
- 文件所有权无冲突；
- Workflow planning/execution 和 Workstream 语义正确；
- route fragment、route record 与 task-unit 接口一致；
- 状态和记录写权限正确；
- 静态检查无 error；
- 无未解释的高风险重复；
- 正向、负向、边界、分支、恢复和失败评测完成；
- 上下游接口一致；
- 未重新引入开发子 Agent、嵌套委派或多个前台 MD 子 Agent。
