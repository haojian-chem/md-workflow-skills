# MD Workflow 四层职责与 Lightweight Runtime 边界

本文件定义 Manager、Workflow、Operation、Validator 的**逻辑职责边界**。

核心原则：

```text
逻辑职责边界 ≠ LLM 对话边界 ≠ 进程边界
```

Lightweight Runtime v2 默认只有两个长期用户对话角色：

```text
Manager 对话
→ Task Sheet
→ Task Execution Agent 对话
```

Task Execution Agent 在执行过程中按当前 Step 加载 Operation / Validator / Tool；这些逻辑层不要求分别创建新的 Agent。

## 1. Manager

唯一主工作：任务级项目管理与初始规划。

负责：

- 确认 Skill root 与 MD project root；
- 定位已有 Task；
- 创建新的独立 Task；
- 使用轻量 planning index 生成初始子环节计划；
- 维护 `task_index.md` 中的任务导航信息；
- 用户明确要求时重新规划或整理任务；
- 将 `Txxxx.md` 一次性交接给 Task Execution Agent。

Manager 不负责：

- 普通 Step 的科学执行；
- 当前 Step 的 reuse 判定；
- 判断某个 Step 对当前体系是否科学适用；
- Operation / Validator 的逐步调度闭环；
- route / Workstream / event / artifact state / runtime task-result；
- 为每个子环节创建任务执行目录；
- 预读全部 Step Skill；
- 为“全面了解”扫描整个项目。

Manager 可以建立或确认稳定 Workflow / Step 基础目录，并在 Task Sheet 中记录：

```text
<base_work_directory>/<task_id>/
```

但具体 `<task_id>/` 由 Task Execution Agent 在确实需要本地执行时创建。

## 2. Workflow

唯一主工作：拥有一个科研阶段的**阶段级科学关系与 Step 映射**。

负责：

- 阶段目标；
- 有序 substep / Step registry；
- Step 与 Operation / Validator Skill 的映射；
- 阶段内上游结果对下游处理的科学关系；
- 哪些科学结果可能导致后续尚未执行 Step 被增加、删除、替换或重排；
- 阶段完成条件；
- 基础工作目录语义。

Workflow 不负责：

- 创建/修改 Task Sheet；
- 返回 route fragment；
- 返回 workflow decision；
- 维护 active route / Workstream / event；
- 直接执行 Operation / Validator；
- 定义具体 Step 的 reuse conditions；
- 为 Manager 提供 `conditional` / applicability 标记；
- 复制 Step 的科学算法；
- 直接根据目录存在判断完成。

当某个 Step 的结果影响后续尚未执行 Step 时，Workflow 可以说明**关系**，但具体适用性判定由相关 Step Skill 和 Task Execution Agent 在执行时完成。

## 3. Operation

唯一主工作：执行一个明确、可核验的业务操作。

负责：

- 当前 Step 的业务 Preflight；
- 明确对象上的文件/命令/结构操作；
- 必要的可复现脚本、配置和中间结果；
- 操作是否实际完成的核验；
- 业务结果文件；
- 在其拥有相应内容时定义 Step 的 object requirements、reuse conditions、execution rules 和 official results。

Operation 不负责：

- 项目级任务规划；
- Workflow 阶段关系；
- route / Workstream / event / runtime task-result；
- 创建嵌套 Agent；
- 无明确依据扩展用户研究目标；
- 在有专属 Validator 时复制其独立 validation rules。

Operation 可以直接由 Task Execution Agent 按 Skill 执行，也可以调用 ACTIVE 且接口合适的确定性 Tool。

## 4. Validator

唯一主工作：读取并检查目标对象，输出科学/技术判定。

负责：

- 目标和必要上下文读取；
- 科学/技术检查、识别、分类或质量判定；
- 区分“Validator 是否成功执行”和“被检查对象是否满足要求”；
- findings、outcome 和必要报告；
- 在其拥有相应内容时定义 validation requirements；
- Validator-only Step 时拥有完整 Step 接口。

Validator 不负责：

- 自动修改被验证对象，除非该 Skill 本身被重新定义为 Operation；
- 项目级任务规划；
- route / Workstream / event / runtime task-result；
- 创建嵌套 Agent；
- 为确认事项绕回 Manager。

需要用户科学判断时，应把触发条件写入 Skill，由当前 Task Execution Agent 在同一个执行对话中向用户确认。

## 5. Step-facing Skill 接口

Workflow 中每个实际子环节都必须由一个 Skill 或一组配套 Skills 合计明确：

```text
purpose
object requirements
reuse conditions
execution rules
validation requirements
official results
```

如果是：

```text
Operation-only Step
```

Operation 通常拥有全部接口。

如果是：

```text
Validator-only Step
```

Validator 拥有全部接口。

如果是：

```text
Operation + dedicated Validator
```

推荐：

- Operation：purpose / object requirements / reuse conditions / execution rules / official results；
- Validator：validation requirements / validation report；
- content map 明确唯一 owner，禁止两份 Skill 复制同一规则。

## 6. Task Execution Agent

Task Execution Agent 是运行角色，不是新的 Skill 层级。

负责在一个长期执行对话中：

1. 读取当前 `Txxxx.md`；
2. 确定当前 Step 和对象；
3. 加载当前 Step 所需 Skill；
4. 查询当前 Step 的历史正式结果；
5. 按 Step reuse conditions 判断；
6. 必要时向用户确认；
7. 执行和验证；
8. 更新 Task Sheet；
9. 登记 official results；
10. 根据结果调整后续 Step；
11. 继续下一 Step，而不是返回 Manager。

它不是独立 authoring layer，也不需要通用 `task_execution_agent/SKILL.md`。

## 7. Tool

Tool 是确定性执行组件，不是第五个科学决策层。

适合：

- parsing；
- hashing；
- deterministic transform；
- 明确格式校验；
- 原子文件写入；
- 重复、稳定、可测试的计算；
- 已冻结规则的机械检查。

Tool 不得：

- 解释用户研究意图；
- 选择任务范围；
- 作开放式科学判断；
- 向用户提问；
- 创建 Agent；
- 为普通 Lightweight 执行强制构造 Legacy task/route/event/transaction 对象；
- 超出注册权限写入。

历史 Tool 如果科学动作仍有价值，但接口依赖 Legacy Runtime，应先适配为显式业务输入接口后再作为 Lightweight 默认路径。

## 8. 目录与写入边界

稳定 Step 基础目录：

```text
<base_work_directory>/
```

可以由项目初始化建立。

任务专属执行目录：

```text
<base_work_directory>/<task_id>/
```

规则：

- Manager 只记录该路径；
- 当前 Step 开始先做 reuse；
- 只有需要实际执行时 Task Execution Agent 才创建该目录；
- 直接复用时不创建空目录；
- 不同 Task 固定文件名结果不得写入同一基础目录。

`00_project_records/**` 的普通维护由 Manager 和当前 Task Execution Agent 按 Lightweight 规则完成；Operation / Validator / Tool 不应绕过执行角色自行建立第二套状态系统。

## 9. 用户确认边界

普通 Step 内的科学歧义由当前 Task Execution Agent 直接向用户确认。

Manager 仅在项目级任务定位、创建、重新规划等管理问题上承担管理对话职责。

Tool 不向用户提问。

Operation / Validator Skill 应声明确认触发条件，但不要求返回 Legacy `confirmation_items` 或 decision record。

## 10. Legacy 边界

以下只属于冻结历史、旧项目迁移或明确 Legacy 维护：

```text
Workstream
Focus
route / route revision
workflow_route_fragment
workflow_decision
subagent_task / subagent_result
project event
artifact state machine
transaction closure
runtime projection orchestration
```

新 Skill 不得因为这些文件仍在仓库中而继续复制旧接口。
