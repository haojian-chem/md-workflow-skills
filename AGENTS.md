# MD Workflow Project Instructions

## 1. 项目范围

本仓库同时用于：

1. 真实 MD 项目的运行时管理；
2. MD Workflow Skill / Tool / contract / runtime projection 的设计与维护。

Skill 架构根目录：

`/root/data/5_codex/3_md_workflow`

真实 MD 项目根目录不固定。运行 Manager 时必须分别确认或读取 Skill root 与 MD project root。

## 2. 先判断当前模式

### REAL_MD_RUNTIME

当用户要求检查、规划、执行、续跑或恢复一个真实 MD 项目时：

1. 读取 `runtime/runtime_manifest.yaml`；
2. 按 manifest 读取最小 runtime spec；
3. 只读取当前项目状态、active route、当前 Workflow runtime spec 和当前 task 直接需要的业务 Skill/records；
4. 不默认读取 `00_authoring/**`、`design_records/**`、完整 authoring references、全部 schemas 或无关 Workflow；
5. 只有 runtime material 缺失/失效、恢复、协议冲突或用户明确要求架构审计时，才回退读取对应权威 authoring source。

真实 runtime 的目标是：把静态规则读取、schema 解释、机械记录构造和重复 Workflow 推理压到最小。

### AUTHORING_OR_MAINTENANCE

当用户要求编写、修改、审查或规划 Skill、Tool、contract、Manager 协议、runtime projection 或整个架构时：

1. 读取 `00_authoring/AUTHORING_RULES.md`；
2. 再读取目标文件对应的 content map、work order、contracts 和权威 references；
3. 修改 runtime projection 时，同时检查其权威 source 与 provenance。

不要把 authoring 规则自动带入真实 MD runtime。

## 3. Runtime 逻辑职责

逻辑职责保持：

```text
Manager
→ Workflow
→ Operation / Validator
```

Tool 是确定性执行组件，不是第五个决策层。

职责边界不等于 LLM 调用边界。运行时可使用：

```text
DETERMINISTIC
AGENT_TASK
AGENT_SEQUENCE
```

具体启用状态、资格与回退规则以 `runtime/runtime_manifest.yaml` 和权威 runtime protocol 为准。

Manager 仍控制项目状态、路线、用户决定和 `00_project_state/**`、`00_project_records/**` 的提交边界；机械 YAML/event/artifact/state 构造可以由已批准的确定性 Tool 完成。

## 4. Runtime 最小原则

- 正常运行优先消费 `runtime/**` 的紧凑投影，不重复阅读完整设计文档；
- schema 由确定性 Tool 消费，不由 LLM 逐字段模拟；
- 确定性文件系统、hash、解析、序列化、直接引用检查优先 Tool；
- active route 未受新证据影响时，允许按已冻结 fast-path 规则推进，不机械重新推理完整 Workflow；
- 只有科学语义、歧义、用户决定、route-changing evidence、恢复和异常状态需要 LLM 语义判断；
- 不在 Manager 初始化阶段解析 PDB/结构业务内容；业务输入检查归对应 Operation/Validator；
- 同时最多一个前台 MD Agent context；外部 tmux/调度任务可并存。

## 5. 通用权限与安全

- 不修改 `01_sources/` 中的来源文件；
- source recognition 默认复制源结构；只有用户明确授权且具备 source write permission 时才允许移动；
- 不自动通过单位计费的期刊数据库下载文献；
- 未经授权，不删除、覆盖或批量移动项目文件；
- 破坏性或不可逆操作由 Manager 汇总后请求用户确认；
- Workflow、Operation、Validator、Tool 和临时子 Agent 不直接向用户请求确认；
- 默认 Tool 不访问网络，也不得嵌入 LLM 调用；
- 写入型 Tool 必须遵守候选、校验、备份/回滚和受控提交规则。

## 6. 架构来源

- runtime 入口：`runtime/runtime_manifest.yaml`
- authoring/maintenance：`00_authoring/AUTHORING_RULES.md`
- 跨 Skill contracts：`03_contracts/`
- Manager：`00_manager/md_workflow_manager/`
- Workflow：`01_workflows/`
- Operation：`02_operations/`
- Validator：`02_validators/`
- Tool：`05_tools/`

`runtime/**` 是权威 source 的紧凑运行时投影，不得成为第二套独立设计源。
