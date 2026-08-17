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
├── references/                 # main Skill 的长/条件性规则
├── assets/                     # 少量当前模板
├── scripts/                    # 少量当前静态检查
├── architecture_freezes/       # Stage / Workflow 正式冻结记录
├── project_design/             # 项目级设计/状态资料，按需读取
├── coordination/               # 多窗口 write ownership / work orders
├── archive/                    # 非 current 历史材料
└── md-workflow-tool-authoring/ # Tool authoring supporting Skill
```

`project_design/` 只保存真正有独立项目级职责的资料：

```text
project_design/
├── README.md
├── MD_WORKFLOW_MASTER_PLAN.md
└── lightweight_runtime_v2_spec.md
```

不再单独维护 current `SYNC_STATUS.md`、`skill_inventory.yaml`、`content_map.schema.yaml` 或 `content_maps/`。

## Scientific Skill layout

当前 active 科研 Skill 按 Stage / 科学职责组织：

```text
01_structure_preparation/
02_topology_preparation/
04_md_simulation/
05_analysis/
```

Manager 自身是独立 Skill package：

```text
00_manager/
├── SKILL.md
└── references/
    └── workflow_plan_index.yaml
```

历史 `01_workflows/`、`02_operations/`、`02_validators/` 已退出 active scientific Skill layout；确需保留的旧 role-split implementation 放入 `archive/` 或由 Git history 保存。

没有 current Skill 实现的 Stage / step 不为了目录对称创建空 package。

## Current Skill model

新科研 Skill 默认采用：

```text
main Skill
├── references/        # 长而仍属于当前职责的细节
├── schemas/           # only when truly useful
├── scripts/           # Skill-local deterministic helper
└── supporting Skill   # only for complex, clear boundaries
```

只有 main `SKILL.md` 是默认必需文件。不要先生成目录、schema 或角色分类，再把科研职责塞进去。

详细规则：

`references/skill_generation_rules.md`

## Agent-guidance principle

Skill 的目的，是指导 Agent 如何处理科研任务，而不是把 Agent 锁进固定 parser / wrapper / dispatcher。

Parser / Tool 用于真正需要确定性 parsing、变换、计算或校验的动作；除非科学 / 技术方法本身要求，不把某个 Tool 写成 Agent 理解输入的唯一入口。

## Multi-window rule

```text
read scope can be broad
write ownership must be narrow
```

每个窗口可以并且应该按需读取不归自己写入的上下游 / 相邻 Skill，以理解接口和避免重复。

未经明确重新分配，不得：

- 修改其他 Skill；
- 在当前 Skill 中替其他 Skill 定义内部流程、默认参数、validation 或 official results；
- 复制 / 改写其他 owner 已有规则形成 shadow specification。

详细协议：

`references/multi_window_authoring_protocol.md`

## Architecture freezes

正式 Stage / Workflow freeze 统一位于：

`architecture_freezes/`

不得把新的 `WORKFLOW*_ARCHITECTURE_FREEZE*.md` 散放到 `00_authoring/` 根目录。

## Project design

- Master Plan 只拥有 Stage catalog / 建设状态 / current entry；
- runtime spec 只拥有跨 Stage Runtime 通用架构；
- 具体业务规则由对应 current Skill / reference 拥有；
- Stage-specific 已冻结架构由 `architecture_freezes/` 拥有。

因此 project-design 文档不是业务 Skill 的第二份规范。

## Archive

被 current authority 明确取代的历史 Markdown 移入 `archive/`；active path 不保留同名 / 同义 tombstone。

Archive 不进入普通 startup/read list。Git history 继续保存完整版本历史。归档依据是 authority 已被取代，不是文件年龄。

## Authority

发生内容冲突时按具体职责判断 owner：

```text
具体业务规则 → current Skill / reference
Stage 已冻结架构 → architecture_freezes/
跨 Stage runtime → project_design/lightweight_runtime_v2_spec.md
Stage catalog / 建设状态 / current entry → project_design/MD_WORKFLOW_MASTER_PLAN.md
历史材料 → archive / Git history
```

同一具体规则只能有一个 current owner。
