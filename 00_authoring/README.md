# Authoring directory guide

`00_authoring/` 服务于 MD Workflow Skill / Tool 的设计、冻结和多窗口 authoring；它不是科研项目运行目录。

## Single authoring entry

新开的 **Skill authoring / maintenance 窗口**首先读取：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

`00_authoring/SKILL.md` 是唯一 authoring 主入口。其他内容由该 Skill 根据当前任务按需引用，不要求启动时预加载整个目录。

`README.md` 只负责给人说明目录，不是第二份 authoring rule authority。

## Current layout

```text
00_authoring/
├── SKILL.md                    # 唯一 authoring main Skill
├── README.md                   # 目录说明
│
├── references/                 # main Skill 的长/条件性规则
├── assets/                     # 少量当前模板
├── scripts/                    # 少量当前静态检查
│
├── architecture_freezes/       # Stage / Workflow 正式冻结记录
├── project_design/             # 项目级设计/状态资料，按需读取
├── coordination/               # 多窗口 write ownership / work orders
├── archive/                    # 非 current 历史 authoring 材料
│
└── md-workflow-tool-authoring/ # Tool authoring supporting Skill
```

`project_design/` 当前只保存真正有独立项目级职责的资料：

```text
project_design/
├── README.md
├── MD_WORKFLOW_MASTER_PLAN.md
└── lightweight_runtime_v2_spec.md
```

不再单独维护 current `SYNC_STATUS.md`；Stage catalog、建设状态和 current entry 统一由 Master Plan 负责。

不再维护 `skill_inventory.yaml`、`content_map.schema.yaml` 或 `content_maps/` 这一套平行 Skill metadata。

多窗口 writer assignment 如确有需要，位于：

`coordination/file_ownership.yaml`

## Current Skill model

新科研 Skill 默认采用：

```text
main Skill
├── references/        # 长而仍属于当前职责的细节
├── schemas/           # only when truly useful
├── scripts/           # Skill-local deterministic helper
└── supporting Skill   # only for complex, clear boundaries
```

只有 main `SKILL.md` 是默认必需文件。不要先生成一套目录、schema 或角色分类，再把科研职责塞进去。

详细生成/重构规则：

`references/skill_generation_rules.md`

当前设计不强制 Workflow / Operation / Validator 分类，也不要求新 Skill 落入：

```text
01_workflows/
02_operations/
02_validators/
```

这些目录仍包含历史时期创建、目前可能仍有效的 Skill，但只是现存物理路径，不是新 authoring 模板。

## Agent-guidance principle

Skill 的目的，是指导 Agent 如何处理科研任务，而不是把 Agent 锁进固定 parser / wrapper / dispatcher。

Parser / Tool 用于真正需要确定性 parsing、变换、计算或校验的动作；除非科学/技术方法本身要求，不把某个 Tool 写成 Agent 理解输入的唯一入口。

## Multi-window rule

```text
read scope can be broad
write ownership must be narrow
```

每个窗口可以并且应该按需读取不归自己写入的上下游/相邻 Skill，以理解接口和避免重复。

未经明确重新分配，不得：

- 修改其他 Skill；
- 在当前 Skill 中替其他 Skill 定义内部流程、默认参数、validation 或 official results；
- 复制/改写其他 owner 已有规则形成 shadow specification。

详细协议：

`references/multi_window_authoring_protocol.md`

## Architecture freezes

正式 Stage / Workflow freeze 统一位于：

`architecture_freezes/`

不得再次把新的 `WORKFLOW*_ARCHITECTURE_FREEZE*.md` 散放到 `00_authoring/` 根目录。

## Project design

项目级设计资料统一位于：

`project_design/`

原则：

- Master Plan 只拥有 Stage catalog / 建设状态 / current entry；
- runtime spec 只拥有跨 Stage Runtime 通用架构；
- 具体业务规则继续由对应 current Skill / reference 拥有；
- Stage-specific 已冻结架构继续由 `architecture_freezes/` 拥有。

因此 project-design 文档不是业务 Skill 的第二份规范。

## Archive

被 current authority 明确取代的历史 authoring Markdown 移入：

`archive/`

规则：

- current 引用先迁移；
- active path 不保留同名/同义 tombstone；
- archive 不进入普通 startup/read list；
- Git history 继续保存完整版本历史；
- 归档依据是 authority 已被取代，不是文件年龄。

## Authority

发生内容冲突时，按具体职责判断 owner，而不是按目录深浅判断：

```text
具体业务规则 → current Skill / reference
Stage 已冻结架构 → architecture_freezes/
跨 Stage runtime → project_design/lightweight_runtime_v2_spec.md
Stage catalog / 建设状态 / current entry → project_design/MD_WORKFLOW_MASTER_PLAN.md
历史材料 → archive / Git history
```

同一具体规则只能有一个 current owner。
