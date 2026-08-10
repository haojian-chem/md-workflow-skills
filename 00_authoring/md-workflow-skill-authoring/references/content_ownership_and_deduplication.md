# 内容唯一归属与去重

## 单一真值

每个概念必须有一个且只有一个 owner。

| 内容 | 权威位置 |
|---|---|
| Lightweight Runtime 总体架构 | `00_authoring/lightweight_runtime_v2_spec.md` |
| 四层逻辑职责 | `references/layer_boundaries.md` |
| Manager 任务管理与初始规划 | `00_manager/md_workflow_manager/SKILL.md` |
| Manager 轻量 planning catalog | `00_manager/md_workflow_manager/references/workflow_plan_index.yaml` |
| Workflow 阶段科学关系与 Step 映射 | 当前 Workflow `SKILL.md` |
| 当前 Step 的执行规则 | 当前 Operation / Validator `SKILL.md` |
| 当前 Step 的 reuse conditions | content map 指定的当前 Step owner |
| 当前 Step 的 validation requirements | 当前 Validator 或明确 owner |
| 当前 Step 的 official results | content map 指定的当前 Step owner |
| 跨任务正式结果检索 | 项目 `project_result_index.md` |
| 当前任务计划与恢复上下文 | 项目 `tasks/Txxxx.md` |
| 网页端多窗口规则 | `references/multi_window_authoring_protocol.md` |
| 确定性 Tool 通用边界 | `references/deterministic_tool_protocol.md` |
| 当前 Tool 接口 | 当前 Tool `tool.yaml` |
| 当前 Skill 独有领域数据 | 当前 `references/` |
| 当前 Skill 独有输出结构 | 当前 `schemas/` |
| 示例和测试数据 | `04_evals/<skill-name>/fixtures/` |

Legacy `03_contracts/**`、runtime projection、subagent protocol、record commit protocol 只在 Legacy 维护时拥有其历史接口，不是 Lightweight 新 Skill 的共享运行时 owner。

## `SKILL.md`

保留：

- 唯一工作；
- 职责边界；
- 当前 Skill 独有输入/对象要求；
- 核心执行或判定步骤；
- reuse conditions（如果本 Skill 是 owner）；
- validation requirements（如果本 Skill 是 owner）；
- official results（如果本 Skill 是 owner）；
- 特有用户确认条件；
- 特有 Preflight；
- 对 reference/schema/Tool 的按需引用。

不得重复：

- 整套 Lightweight Runtime 规则；
- 其他 Step 的详细算法；
- Task Sheet 通用字段定义；
- project_result_index 通用格式；
- 另一个 Skill 已拥有的 reuse / validation / official result 规则；
- Legacy route / Workstream / event / task-result contract。

## Workflow `SKILL.md`

只保存阶段级内容：

- 阶段目标；
- Step 顺序与映射；
- conditional Step 列表；
- 阶段内科学关系；
- 阶段完成条件。

不得复制每个 Step 的：

- object requirements；
- reuse conditions；
- Preflight；
- 命令；
- schema 字段；
- official result 细节。

## Operation + Validator 配套

同一 Step 有 Operation 和专属 Validator 时，推荐唯一归属：

```text
Operation
→ purpose
→ object requirements
→ reuse conditions
→ execution rules
→ official results

Validator
→ validation requirements
→ validation report / findings
```

如果实际职责不同，可以调整，但必须在 content map 明确唯一 owner。

不要在 Operation 和 Validator 两边分别完整写同一套 Step contract。

## `references/`

只保存当前 Skill 独有且按需读取的：

- 科学规则；
- registry；
- 长说明；
- 专用数据表；
- 方法细节。

Reference 不重新描述 `SKILL.md` 的完整执行流程。

## `schemas/`

只在当前 Skill 产生独有结构化文件且字段约束确有价值时创建。

Lightweight Runtime 不需要给 Task Sheet、route、subagent task/result 建立新的本地 schema 副本。

跨 Step 的 handoff 优先通过上游已经定义的 official result 文件完成。

## `scripts/`

只保存当前 Skill 独有且不值得共享的确定性实现。

跨 Skill 可复用的稳定程序进入 `05_tools/`。

不要为了旧 Runtime wrapper 保留新的多层 adapter；新 Lightweight Tool 应优先接受明确业务输入和输出路径。

## 示例与评测

示例统一进入 fixture / eval，不与 schema 并行维护第二套约束。

Lightweight Step 评测优先覆盖：

- reuse；
- task-scoped 目录；
- official results；
- 用户确认；
- 跨对话恢复；
- 不写 Legacy runtime records。

## 拆分警告

出现以下情况时必须重构：

- 同一规则在两个文件完整出现；
- Workflow 开始复制 Step 详细科学逻辑；
- Operation 与 Validator 重复定义同一 validation/reuse 规则；
- 主流程被字段表或大枚举淹没；
- 修改一个定义需要同步多个位置；
- reference 重新描述 `SKILL.md` 的完整流程；
- schema 与示例各自定义不同约束；
- 新 Skill 为兼容 Legacy Runtime 又复制 route/task/result/event 接口；
- 每个 Task 的固定输出仍写入共同 Step 基础目录而不是 `<task_id>/`。
