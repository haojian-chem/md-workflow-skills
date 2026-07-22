# 内容唯一归属与去重

## 单一真值

每个概念必须有一个且只有一个 owner。

| 内容 | 权威位置 |
|---|---|
| 四层职责 | `references/layer_boundaries.md` |
| 运行时子 Agent 生命周期 | `references/runtime_subagent_protocol.md` |
| 网页端多窗口规则 | `references/multi_window_authoring_protocol.md` |
| 通用状态和文件记录 | `03_contracts/common_types.schema.yaml` |
| 用户确认项 | `03_contracts/confirmation_item.schema.yaml` |
| Workflow 当前决策 | `03_contracts/workflow_decision.schema.yaml` |
| 临时子 Agent 输入 | `03_contracts/subagent_task.schema.yaml` |
| 临时子 Agent 返回 | `03_contracts/subagent_result.schema.yaml` |
| 全局项目状态 | `03_contracts/project_state.schema.yaml` |
| 当前 Skill 局部流程 | 当前 `SKILL.md` |
| 当前 Skill 独有领域数据 | 当前 `references/` |
| 当前 Skill 独有输出结构 | 当前 `schemas/` |
| 示例和测试数据 | `04_evals/<skill-name>/fixtures/` |

其他位置只引用，不复述完整定义。

## `SKILL.md`

保留：

- 唯一工作；
- 职责边界；
- 特有输入；
- 核心执行步骤；
- 特有条件和阻塞；
- 输出路径；
- 特有自检；
- 对共享 contract 和 reference 的按需引用。

不得重复：

- `DONE/BLOCKED/FAILED` 定义；
- 通用确认项字段；
- 运行时子 Agent 任务包字段；
- 项目级文件所有权规则；
- 其他 Skill 的详细步骤。

## `references/`

只保存当前 Skill 独有且按需读取的领域规则、注册表或长说明。

Registry 只保存数据，不写执行流程。

## `schemas/`

只在 Skill 生成独有结构化输出时创建。

跨 Skill 的任务和返回结构不得复制到本地 schema。

## 示例

示例不与 schema 并行维护。示例统一成为评测 fixture，由测试验证其符合 schema。

## 拆分警告

出现以下情况时必须重构：

- 同一规则在两个文件完整出现；
- 主流程被字段表或大枚举淹没；
- 修改一个定义需要同步多个位置；
- reference 重新描述 `SKILL.md` 的完整流程；
- schema 与示例各自定义不同约束；
- 每个 Skill 复制同一返回 YAML。
