# MD Workflow Authoring Rules

本文件保存 Skill/Tool 设计、实现、审查和多窗口协作规则。它属于 **AUTHORING_ONLY** 材料。

真实 MD 项目运行时不得默认读取本文件；只有用户正在编写、修改、审查 Skill/Tool、contract、runtime spec 或架构规则时才读取。

## 1. 开发与运行分离

### Skill 开发

- 用户可以在网页端打开多个独立窗口；
- 每个窗口只编写被分配的 Skill 或互斥文件范围；
- 网页窗口不是运行时 Agent；
- 项目中不得为编写窗口创建开发子 Agent 角色或配置。

### Tool 开发

- 共享 Tool 统一位于 `05_tools/`；
- Tool 生成、修改、测试、注册、升级和废弃由 `00_authoring/md-workflow-tool-authoring/SKILL.md` 管理；
- 业务 Skill 可以提出 `tool_request`，但不得在运行中的业务 task 内临时修改共享 Tool；
- 未测试 Tool 不得标记为 `ACTIVE` 或作为默认生产路径。

### Runtime layer 开发

- `runtime/**` 是由权威 authoring sources 派生的紧凑运行时投影，不是第二套独立设计源；
- runtime spec 的语义变更必须先修改对应权威 source，再重新生成/同步 runtime projection；
- 在自动 compiler 尚未实现前允许 `bootstrap_curated` 投影，但必须记录 source paths 与 Git blob provenance；
- 不允许只改 `runtime/**` 而不检查对应权威 source 是否需要同步。

## 2. 权威文件

跨 Skill 的状态、Focus、Workflow route fragment、Workflow decision、task unit、子 Agent 返回、项目与 Workstream 状态、事件、路线、决策、submission、artifact set 和 snapshot 由：

`03_contracts/`

定义。入口索引为：

`03_contracts/README.md`

跨 Workflow 路线规划规则由：

`00_manager/md_workflow_manager/references/route_planning_protocol.md`

定义。

四层职责、运行时子 Agent 协议、确定性 Tool 协议、内容归属和多窗口编写规则由：

`00_authoring/md-workflow-skill-authoring/references/`

定义。

项目记录/恢复设计由：

`design_records/`

定义。

Tool 注册状态、版本、入口和权限由：

`05_tools/tool_registry.yaml`

定义。

具体 Skill 和 Tool 只能引用，不得复制并重新定义共享规则。

`runtime/**` 只能保存上述权威文件的紧凑运行时投影与 provenance。

## 3. 四层职责与 Tool 边界

逻辑职责保持：

```text
Manager
Workflow
Operation
Validator
```

Tool 是确定性程序，不是第五个决策层。

职责边界不自动等于 LLM 调用边界。运行时执行后端可以是：

```text
DETERMINISTIC
AGENT_TASK
AGENT_SEQUENCE
```

具体语义由 `runtime_subagent_protocol.md` 和 runtime projection 定义。

Workflow 不执行 Operation/Validator，不创建项目 Focus，不创建 Workstream，也不拼接其他 Workflow。

Manager 不得根据阶段名称自行编造 Workflow 内部步骤，也不得脱离 execution decision/active-route fast-path 规则自行选择局部业务步骤。

Tool 不得向用户提问、创建 Agent、降低 gate 或修改注册权限之外的路径。

## 4. 路线规划规则

- 每个 Workflow 只生成自身阶段的 `workflow_route_fragment`；
- Manager 解析起点、终点和停止条件；
- Manager 按 stage registry 确定涉及的 Workflow；
- 相邻 fragment 的 exit artifact 必须满足下一 fragment 的 entry requirement；
- 条件步骤标记 `REQUIRED | CONDITIONAL`；
- 无证据时不得提前删除条件步骤；
- 未连接 Workflow 在边界形成 `PARTIAL | BLOCKED`，不得虚构内部步骤；
- route record 创建后不可覆盖，修订通过新 route 和 `supersedes` 表达；
- execution evidence 与 active route 冲突时必须进入 Workflow/Manager 语义重判或暂停；
- 预计路线是动态投影，不是硬编码批处理队列。

## 5. 项目状态、记录与确定性校验

Manager 是以下目录的唯一提交授权者：

```text
00_project_state/**
00_project_records/**
```

Operation 和 Validator：

- 只能在 task unit 授权的业务路径写入；
- 不得修改项目状态或结构化历史记录；
- 只返回候选 artifact、决策请求和详细业务日志路径。

“Manager owns records”表示 Manager 控制提交边界，不要求 Manager LLM 手工构造全部 YAML。机械记录构造应优先由确定性 builder/recorder 完成。

外部任务从 `RUNNING` 结束后必须先进入 `FINISHED_UNVERIFIED`，完成输出核验后才能标记为 `COMPLETED` 或 `FAILED`。

runtime schema 校验原则：

```text
FAST：普通 changed runtime instances + 直接引用
FULL：恢复、contract/schema 变化和明确关键生命周期节点
```

NEW 初始化的最终校验模式由 runtime redesign 的 R6 冻结；不得因为旧文档历史习惯机械执行 FULL。

- 普通 task 不得执行 FULL contract validation；
- schema 文件 hash 未变化且 cache 有效时，不重复 schema meta-validation；
- 不得用 LLM 逐字段模拟 schema 或全项目引用校验；
- Tool cache 是非权威数据，必须可删除和重建。

## 6. 修改前回顾

提出或实施新方案前，先列出：

```text
已做过
已否定
仍未验证
```

若新方案与已失败方案重复或本质等价，且没有新证据改变前提，不得再次执行。

## 7. 内容唯一归属

一条规则只能有一个权威位置：

- 项目模式路由与最小通用安全规则：根 `AGENTS.md`；
- authoring/development 规则：本文件及 authoring references；
- 跨 Skill 接口：`03_contracts/`；
- 跨 Workflow 路线拼接：Manager route planning protocol；
- 确定性 Tool 运行边界：`deterministic_tool_protocol.md`；
- Tool 注册与版本：`05_tools/tool_registry.yaml`；
- 阶段内路线片段和执行逻辑：对应 Workflow `SKILL.md`；
- 当前 Operation/Validator 的执行逻辑：当前 `SKILL.md`；
- 当前 Tool 的输入输出、权限和实现：当前 `tool.yaml` 与实现文件；
- 当前 Skill 独有领域数据：当前 `references/`；
- 当前 Skill 独有输出结构：当前 `schemas/`；
- 示例与评测夹具：`04_evals/<skill-or-tool-name>/fixtures/`；
- 真实 MD runtime 的紧凑投影：`runtime/**`，仅派生不独立拥有设计语义。

其他文件只引用，不复述完整定义。

## 8. 多窗口文件所有权

- 新窗口开始前读取 `00_authoring/SYNC_STATUS.md`、`skill_inventory.yaml`、`file_ownership.yaml`、目标 content map、work order 和适用 contracts；
- 涉及 Workflow 或路线时读取 route planning protocol；
- 涉及 Tool 时读取 deterministic tool protocol 和 tool registry；
- 涉及 runtime projection 时读取对应 source 与 `runtime/runtime_manifest.yaml`；
- 同一文件同一时间只有一个编写窗口；
- 一个 Skill 或 Tool 目录默认只有一个编写窗口；
- `AGENTS.md`、`03_contracts/`、authoring references、Manager references、design records、content maps、inventory、ownership 表、runtime manifest 和 tool registry 只由主窗口修改；
- 写入路径重叠时不得同时编写；
- 共享 contract 的变更由业务窗口提交请求，主窗口统一裁决。

## 9. Workstream 分支规则

已生成有效下游产物、已启动 EM/NVT/NPT/MD、需要保留旧参数或需要比较方案时，不得把项目唯一阶段“回退”并覆盖旧结果。

应从明确 artifact 节点创建新 Workstream。

只有当前步骤尚未闭合、没有有效下游依赖且修改不会影响其他结果时，才允许在原 Workstream 内修正。

## 10. 权限与安全

- 不修改 `01_sources/` 中的来源文件；
- source recognition 默认复制源结构并校验 SHA-256；只有明确用户授权和 source write permission 同时存在时才允许移动；
- 不自动通过单位计费的期刊数据库下载文献；
- 未经授权，不删除、覆盖或批量移动项目文件；
- 破坏性或不可逆操作由 Manager 汇总后请求用户确认；
- Workflow、Operation、Validator、Tool 和临时子 Agent 均不直接向用户请求确认；
- 默认 Tool 不访问网络，也不得嵌入 LLM 调用；
- 写入型 Tool 必须使用候选文件、校验、备份/回滚和受控提交。

## 11. Authoring 完成定义

Skill、Tool 或 runtime projection 只有在适用条件满足后才可通过：

- 层级/Tool/执行后端边界已确认；
- 局部 contract/content map 或 tool.yaml 已确认；
- 文件所有权无冲突；
- Workflow planning/execution、Workstream、Manager 和执行后端语义正确；
- Tool 不承担语义决策或科学判断；
- route fragment、route record 与 task-unit 接口一致；
- 状态和记录写权限正确；
- 静态检查无 error；
- 无未解释的高风险重复；
- 正向、负向、边界、分支、恢复和失败评测完成；
- Tool 的 cache、权限、版本、benchmark 和回退路径已验证；
- runtime projection 可追溯到权威 source 且不存在静默漂移；
- 上下游接口一致；
- 未重新引入嵌套委派或多个前台 MD Agent。
