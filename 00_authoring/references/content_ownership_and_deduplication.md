# 内容唯一归属与去重

Status: CURRENT

## 1. 单一真值

每个 current 规则必须有一个且只有一个 owner。Owner 按具体职责确定，不按 Workflow / Operation / Validator 分类。

常见 authority：

| 内容 | 权威位置 |
|---|---|
| Lightweight Runtime 总体架构 | `00_authoring/project_design/lightweight_runtime_v2_spec.md` |
| Stage catalog / 建设状态 / current entry | `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` |
| Skill 组织与职责边界 | `00_authoring/references/skill_boundaries.md` |
| Manager 任务管理与初始规划 | `00_manager/SKILL.md` |
| Manager planning catalog | `00_manager/references/workflow_plan_index.yaml` |
| 当前科研职责主线 | 当前 main `SKILL.md` |
| 当前职责的长规则 / registry | 当前 `references/` |
| 当前职责独有且稳定的结构化约束 | 当前 `schemas/` |
| Skill-local deterministic helper | 当前 `scripts/` |
| current 跨 Skill deterministic capability | `tools/` 对应 Tool |
| evaluation / fixtures / benchmark | `evals/` |
| Legacy contracts / runtime / tools | `legacy/` |
| 历史 authoring/design material | `00_authoring/archive/` |
| 跨任务正式结果检索 | 项目 `project_result_index.md` |
| 当前任务计划与恢复上下文 | 项目 `tasks/Txxxx.md` |

`legacy/contracts/**`、`legacy/runtime/**`、`legacy/tools/**` 只在明确 Legacy 维护/迁移时拥有其历史接口，不是新 Skill 的共享运行时 owner。

## 2. Rule ownership gate

向当前 Skill 增加任何科学、执行、validation、结果或文件生命周期规则前先判断：

```text
这条规则描述当前 Skill 自己必须如何处理 / 判断 / 产出？
├─ 是 → 当前 Skill 可以定义
└─ 否
   ↓
   是否已有其他 Skill / Tool / shared reference 拥有？
   ├─ 有 → 只引用 owner，不复制 / 改写成第二份规范
   └─ 没有或冲突 → 记录 cross-skill finding，交给对应 owner 裁决
```

最重要边界：

```text
当前 Skill 可以定义：我需要外部 Skill 提供什么
当前 Skill 不可以定义：外部 Skill 应该怎样把它做出来
```

读取权不是定义权。

## 3. 禁止 shadow specification

以下属于 shadow specification：

- 完整复制另一个 Skill 的步骤；
- 重新写一份对方参数表；
- 在当前 Skill 中重新规定对方 validation；
- 复制对方 official-result lifecycle；
- 用 YAML/index 再描述一遍 Skill 已经拥有的职责和状态；
- 简化重述到足以独立指导外部 Skill 内部执行。

允许的接口级描述只有：

```text
consume
require
handoff
```

## 4. Main Skill / reference / supporting Skill

main Skill 保留当前职责的目标、输入、reuse、核心规则、validation、results/handoff、用户确认条件和按需 capability references。

长而仍属于当前职责的内容放 `references/`，但 reference 不重新描述完整主流程。

Supporting Skill 只有复杂且独立时才拆；不得为了形成 Operation + Validator、目录对称或旧角色分类而拆。

## 5. `schemas/` 与 `scripts/`

`schemas/` 只用于确有稳定、机器可校验的 handoff/文件约束，不为了形式化普通自然语言规则而创建。

Skill-local deterministic helper 可以留在当前 `scripts/`；跨 Skill 复用、需要独立生命周期的 current shared Tool 才进入 `tools/`。

## 6. Tool / eval / legacy boundary

```text
tools/   current shared deterministic capability
evals/   tests / fixtures / validation evidence / benchmark
legacy/  historical executable/runtime/contracts/tools
```

三者都不属于 Stage 1–5 Skill roots，不使用 Stage 编号前缀。

旧 Tool 若仍依赖 Workstream、route、runtime task-result、project event、transaction closure 或 old contracts，只能留在 `legacy/tools/`，直到明确完成 current interface adaptation + testing + reactivation。

## 7. Validation ownership

默认：

```text
结果 owner
→ 同时拥有该结果的 validation requirement
```

Tool 负责自己 deterministic 输出的机械/格式有效性；main Skill 负责科研有效性。

## 8. 完成前自检

```text
1. 是否写了其他环节“应该怎么做”？
2. 是否复制 / 改写了另一个 owner 已定义的规则？
3. 是否一条规则以后需要同步更新多个 current owners？
4. 外部内容能否缩成 consume / require / handoff？
5. 是否又建立 metadata/index 来重复 Skill 本身？
6. 是否误把 evals/tools/legacy 当成 Stage Skill root？
```

任一答案为“是”时先处理 ownership / layout 问题。
