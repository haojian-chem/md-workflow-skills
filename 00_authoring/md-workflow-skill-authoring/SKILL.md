---
name: md-workflow-skill-authoring
description: 设计、拆分、编写或重构本项目的 MD manager、workflow、operation、validator Skill 时使用；同时约束 Workstream 状态、串行临时子 Agent 接口和网页端多窗口文件所有权。不要用于运行具体 MD 任务。
---

# 目标

将 MD 工作流需求转化为职责清晰、内容不重复、接口一致的 Skills，并保证：

- Workflow 保留为可复用阶段决策层，但不成为 Agent；
- Workstream 表示真实项目中的具体工作分支；
- Manager 可依据 Workflow 决策串行创建一个上下文连续 task unit；
- task unit 可以是 Operation、Validator 或 Operation 与专属 Validator；
- 临时子 Agent 用于隔离上下文，不用于前台并行；
- 多个 Workstream 和多个外部 tmux/调度任务可以并存；
- 网页端多个编写窗口与运行时子 Agent 完全分离。

# 启动前检查

读取：

1. 项目根 `AGENTS.md`；
2. `00_authoring/SYNC_STATUS.md`；
3. `00_authoring/skill_inventory.yaml`；
4. `00_authoring/file_ownership.yaml`；
5. 目标 Skill 的 content map；
6. 目标窗口的 work order；
7. `03_contracts/README.md` 与适用 schema；
8. 相关上下游 Skill。

先列出：

```text
已做过
已否定
仍未验证
```

缺少 content map、work order、适用共享 contract 或唯一写入权限时，返回 `BLOCKED`。

# 步骤 1：确定层级

需要区分 manager、workflow、operation、validator 时，读取：

`references/layer_boundaries.md`

输出：

```yaml
skill_name:
skill_layer:
primary_job:
nearest_neighbor_skills: []
responsibility_conflicts: []
```

一个 Skill 同时承担多个层级主职责时，先拆分。

# 步骤 2：确认运行时关系

涉及 Manager、Workflow、Workstream 或临时子 Agent 时，读取：

`references/runtime_subagent_protocol.md`

必须满足：

- Workflow 只对一个 Workstream 返回局部决定；
- Manager 负责 Focus、Workstream、状态和记录；
- 任意时刻最多一个前台 MD 临时子 Agent；
- task unit 只能是 Operation、Validator 或 Operation 与其专属 Validator；
- Operation 与 Validator 的结果必须分开；
- 子 Agent 不再委派；
- 子 Agent 不直接修改项目状态和记录目录；
- 详细过程落盘，返回精简摘要；
- 多个外部 MD 任务可并存，但不高频轮询。

# 步骤 3：冻结局部 contract

在编写正文前确认：

```yaml
skill_name:
skill_layer:
job:
trigger_when: []
do_not_trigger_when: []
required_inputs: []
conditional_inputs: []
optional_inputs: []
outputs: []
side_effects: []
write_paths: []
read_paths: []
forbidden_paths: []
blocking_conditions: []
user_confirmation_conditions: []
done_when: []
upstream_dependencies: []
downstream_consumers: []
shared_contracts: []
workstream_effects: []
record_effects: []
```

共享状态和接口只引用 `03_contracts/`。

# 步骤 4：建立内容归属

使用：

`assets/content_map.template.yaml`

详细规则见：

`references/content_ownership_and_deduplication.md`

每个概念只能有一个 owner。发现重复定义时先重构，不继续扩写。

# 步骤 5：设计文件结构

按需创建：

```text
<skill-name>/
├── SKILL.md
├── references/
├── schemas/
├── scripts/
├── assets/
└── agents/
```

仅创建实际需要的目录。`agents/openai.yaml` 仅用于 Skill 元数据、调用策略或工具依赖，不用于定义开发子 Agent。

渐进披露规则见：

`references/progressive_disclosure.md`

# 步骤 6：分配网页窗口

使用：

`assets/window_work_order.template.md`

规则见：

`references/multi_window_authoring_protocol.md`

每个窗口必须有互斥的 `write_paths`。共享文件仅由主窗口修改。

# 步骤 7：编写

选择模板：

- `assets/manager_skill.template.md`
- `assets/workflow_skill.template.md`
- `assets/operation_skill.template.md`
- `assets/validator_skill.template.md`

要求：

- 使用命令式步骤；
- 区分必需、条件和可选输入；
- 明确读写边界；
- 说明已有结果、Workstream 分支和续跑；
- 确认项返回 Manager；
- 不复制共享 contract；
- 仅在实际需要时读取特定 reference；
- 不将网页窗口写成 Agent；
- 不将 Workflow 写成 Agent；
- 不引入多个前台 MD 子 Agent；
- 不把多个外部任务并存误写成前台 Agent 并行。

# 步骤 8：检查

运行：

```bash
python 00_authoring/md-workflow-skill-authoring/scripts/validate_md_skill.py \
  <project-root> <skill-directory>

python 00_authoring/md-workflow-skill-authoring/scripts/detect_cross_file_duplication.py \
  <skill-directory>

python 00_authoring/md-workflow-skill-authoring/scripts/validate_architecture_separation.py \
  <project-root>

python 00_authoring/md-workflow-skill-authoring/scripts/validate_content_maps.py \
  <project-root>
```

修改 `03_contracts/` 后还需运行：

```bash
python 00_authoring/md-workflow-skill-authoring/scripts/validate_contracts.py \
  <project-root>
```

# 步骤 9：评测

示例和夹具统一放入：

`04_evals/<skill-name>/fixtures/`

至少覆盖：

- 正向与负向触发；
- 最近邻边界；
- 必需或条件输入缺失；
- `BLOCKED` 与 `FAILED`；
- 用户决策请求；
- 已有结果、Workstream 分支与续跑；
- Focus 选择；
- Workflow 决策；
- 三种 task unit；
- Operation 与 Validator 结果分离；
- 外部任务 `FINISHED_UNVERIFIED`；
- 子 Agent 禁止写管理目录。

# 交付

网页窗口返回：

```yaml
status: DRAFTED | REVIEW_REQUIRED | BLOCKED
skill_name:
window_id:
owned_paths: []
created_files: []
modified_files: []
validation:
  errors: []
  warnings: []
duplication_findings: []
contract_change_requests: []
open_questions: []
next_action:
```

# 完成条件

- 层级和单一职责已确认；
- 局部 contract 与 content map 已确认；
- 文件所有权无冲突；
- Workflow、Workstream、Manager 和临时子 Agent 的边界正确；
- 主文件与附属文件无重复定义；
- 静态检查和行为评测通过；
- 未出现开发子 Agent、嵌套委派或多个前台 MD 子 Agent 残留。
