# MD Workflow Skill Project Instructions

## 1. 项目范围

本仓库用于设计、实现、审查和维护分子动力学工作流 Skills。

Skill 架构根目录：

`/root/data/5_codex/3_md_workflow`

真实 MD 项目根目录不固定。运行 Manager 时必须分别确认 Skill 架构根目录与真实 MD 项目根目录。

## 2. 两类活动必须分开

### MD 运行时

- 主智能体读取 Manager 与 Workflow Skills；
- Workflow 只返回当前阶段的下一任务决定；
- Manager 每次只创建一个临时子 Agent；
- 临时子 Agent 只执行一个 Operation 或 Validator Skill；
- 子 Agent 用于上下文隔离，不用于并行；
- 子 Agent 不得继续委派；
- 子 Agent 不直接与用户交互。

### Skill 开发时

- 用户可以在网页端打开多个独立窗口；
- 每个窗口只编写被分配的 Skill；
- 网页窗口不是运行时 Agent；
- 项目中不得为编写窗口创建开发子 Agent 角色或配置。

## 3. 权威文件

跨 Skill 的状态、确认项、Workflow 决策、子 Agent 任务包、子 Agent 返回和项目状态只由：

`03_contracts/`

定义。

四层职责、运行时子 Agent 协议、内容归属和多窗口编写规则只由：

`00_authoring/md-workflow-skill-authoring/references/`

定义。

具体 Skill 只能引用，不得复制并重新定义。

## 4. 四层关系

```text
manager → workflow decision → temporary subagent → operation | validator
```

含义：

- Manager 负责全局状态、用户交互和临时子 Agent 生命周期；
- Workflow 负责阶段内下一任务、条件、跳过、gate 和完成判断；
- Operation 负责具体文件或命令操作；
- Validator 负责检查与结构化判定。

Workflow 不执行 Operation/Validator，不创建子 Agent，也不是 Agent。

Manager 不得脱离 Workflow 决策自行选择局部业务步骤。

## 5. 修改前回顾

提出或实施新方案前，先列出：

```text
已做过
已否定
仍未验证
```

若新方案与已失败方案重复或本质等价，且没有新证据改变前提，不得再次执行。

## 6. 内容唯一归属

一条规则只能有一个权威位置：

- 项目通用规则：`AGENTS.md` 或 authoring references；
- 跨 Skill 接口：`03_contracts/`；
- 当前 Skill 的执行逻辑：当前 `SKILL.md`；
- 当前 Skill 独有领域数据：当前 `references/`；
- 当前 Skill 独有输出结构：当前 `schemas/`；
- 示例与评测夹具：`04_evals/<skill-name>/fixtures/`。

其他文件只引用，不复述完整定义。

## 7. 多窗口文件所有权

- 同一文件同一时间只有一个编写窗口；
- 一个 Skill 目录默认只有一个编写窗口；
- `AGENTS.md`、`03_contracts/`、authoring references、inventory 和 ownership 表只由主窗口修改；
- 写入路径重叠时不得同时编写；
- 共享 contract 的变更由业务窗口提交请求，主窗口统一裁决；
- 网页窗口之间不通过开发子 Agent 配置协调。

## 8. 权限与安全

- 不修改 `01_sources/` 中的来源文件；
- 不自动通过单位计费的期刊数据库下载文献；
- 未经授权，不删除、覆盖或批量移动项目文件；
- 破坏性或不可逆操作由 Manager 汇总后请求用户确认；
- Workflow、Operation、Validator 和临时子 Agent 均不直接向用户请求确认。

## 9. 完成定义

Skill 只有在以下条件全部满足时才可通过：

- 层级与局部 contract 已确认；
- content map 已确认；
- 文件所有权无冲突；
- 静态检查无 error；
- 无未解释的高风险重复；
- 正向、负向、边界和失败评测完成；
- 上下游接口一致；
- 未重新引入已移除的开发子 Agent 架构。
