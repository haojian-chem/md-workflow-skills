# 内容唯一归属与去重

Status: CURRENT

## 1. 单一真值

每个当前规则必须有一个且只有一个 owner。

当前 owner 类型按**具体内容职责**确定，不按 Workflow / Operation / Validator 分类确定。

常见 authority：

| 内容 | 权威位置 |
|---|---|
| Lightweight Runtime 总体架构 | `00_authoring/lightweight_runtime_v2_spec.md` |
| Skill 组织与职责边界 | `references/skill_boundaries.md` |
| Manager 任务管理与初始规划 | `00_manager/md_workflow_manager/SKILL.md` |
| Manager 轻量 planning catalog | `00_manager/md_workflow_manager/references/workflow_plan_index.yaml` |
| 当前科研职责主线 | 当前 main `SKILL.md` |
| 当前职责的长科学规则/registry | 当前 `references/` |
| 当前职责独有且稳定的结构化约束 | 当前 `schemas/` |
| Skill-local deterministic helper | 当前 `scripts/` |
| 跨 Skill deterministic capability | `05_tools/` 对应 Tool |
| 跨任务正式结果检索 | 项目 `project_result_index.md` |
| 当前任务计划与恢复上下文 | 项目 `tasks/Txxxx.md` |
| 网页端多窗口规则 | `references/multi_window_authoring_protocol.md` |

Legacy `03_contracts/**`、runtime projection、subagent protocol、route/event/transaction 文件只在明确 Legacy 维护时拥有其历史接口，不是新 Skill 的共享运行时 owner。

## 2. Rule ownership gate

**向当前 Skill 增加任何科学、执行、validation、结果或文件生命周期规则之前，都必须先做 ownership 判断。**

```text
准备加入一条规则
↓
这条规则是否描述“当前 Skill 自己必须如何处理/判断/产出”？
├─ 是
│  → 当前 Skill 可以定义
│
└─ 否
   ↓
   是否已有其他 Skill / Tool / shared reference 拥有这条规则？
   ├─ 有
   │  → 只引用 owner 的正式结果、能力或规则入口
   │  → 不复制、不改写成第二份规范
   │
   └─ 没有或存在冲突
      → 记录 cross-skill finding / handoff
      → 交给对应 owner window / main window 裁决
      → 不在当前 Skill 中临时创造一份“兼容规则”
```

最重要的边界是：

```text
当前 Skill 可以定义：
“我需要外部 Skill 提供什么”

当前 Skill 不可以定义：
“外部 Skill 应该怎样把它做出来”
```

读取外部 Skill 的目的，是准确理解它已经提供什么、避免重复和保证 handoff；**读取权不是定义权。**

## 3. 禁止 shadow specification

不得为了让当前 Skill 看起来“自洽”而建立外部规则的第二份规范，即使只是改写措辞。

以下都属于 shadow specification：

- 完整复制另一个 Skill 的步骤；
- 把另一个 Skill 的参数表重新写一遍；
- 在当前 Skill 中总结并重新规定对方的 validation；
- 复制对方的 official-result 结构或文件生命周期；
- 把外部规则“简化重述”到足以独立指导执行，从而形成第二个 authority。

允许的最小接口描述只有：

```text
consume: 使用哪个正式结果
require: 需要哪项已冻结能力/判据
handoff: 当前输出如何交给下游
```

必要时可以说明为什么需要该接口，但不要展开 owner Skill 的内部实现。

如果一句接口说明已经开始出现“对方先做 A，再做 B，参数用 C，最后检查 D”，通常说明已经越界。

## 4. Main `SKILL.md`

主 Skill 保留：

- 当前任务目标；
- scope / responsibility boundary；
- 当前输入/对象/证据要求；
- reuse 判据；
- 核心执行/判断主线；
- validation；
- 结果与 handoff；
- 特有用户确认条件；
- 对 reference / supporting Skill / Tool 的按需引用。

主 Skill 不应重复：

- 整套 Runtime 架构；
- 其他 Skill 的内部算法；
- 其他 Skill 的默认参数、validation、official results；
- Tool 已完整拥有的确定性接口实现；
- Legacy route / Workstream / event / task-result contract。

## 5. Supporting Skill

只有复杂且边界清晰时才拆 supporting Skill。

Supporting Skill 必须拥有一项可独立描述的完整职责，不能只是：

- 为了形成“Operation + Validator”配对；
- 为了把主 Skill 的几条规则搬出去；
- 为了匹配 `01_workflows/02_operations/02_validators` 目录；
- 为了增加一个 dispatcher hop。

Main Skill 只引用 supporting Skill 的能力和 handoff，不复制其内部完整规则。

## 6. 外部 Skill 的接口级描述

当前 Skill 可以读取并理解其他 Skill，但只拥有与自身相关的**接口关系**。

允许记录：

```text
consume: 上游哪个正式结果
require: 外部 Skill 的哪项已冻结能力
handoff: 当前输出如何供下游使用
```

禁止在当前 Skill 中重新定义外部 Skill 的：

```text
内部步骤
默认参数
方法选择
validation
结果文件生命周期
official results
任务计划规则
```

发现外部 Skill 缺失/冲突时，写 cross-skill finding / handoff 给其 owner，不在当前文件中建立第二份规则。

## 7. `references/`

适合保存当前 Skill 独有且按需读取的：

- 长科学规则；
- registry；
- 数据表；
- 长方法说明；
- 大枚举；
- 只有特定条件才需要的细节。

Reference 不重新描述 `SKILL.md` 的完整主流程。

## 8. `schemas/`

只在确有稳定、可机器校验的结构化 handoff/文件约束时创建。

不要把本可以由 Agent 直接理解的普通文本描述强制转换成 schema，只为了让流程看起来形式化。

不要为 Task Sheet、route、subagent task/result 等重新建立 Legacy 式本地 schema 副本。

## 9. `scripts/` 与 Tool

Skill-local、不会跨 Skill 复用的小型确定性 helper 可以留在 `scripts/`。

跨 Skill 复用、需要独立测试与生命周期的确定性程序进入 `05_tools/`。

Tool 的存在不代表当前 Skill 必须通过它才能理解任务；是否强制调用由当前科学/技术要求决定。

## 10. Validation ownership

默认：

```text
结果 owner
→ 同时拥有该结果的 validation requirement
```

只有 validation 本身复杂、可复用、边界清晰时才拆 supporting validation Skill。

Tool 对自己生成的确定性输出负责机械/格式有效性；main Skill 对这些输出是否满足当前科研目标负责。

## 11. Content map

Content map 只记录：

- 当前 Skill 路径；
- 当前 owned content；
- supporting/reference ownership；
- 外部只读 authority。

新 content map 不要求 `skill_type: workflow|operation|validator`。

Content map 不是任务运行时 dispatcher，也不应把其他 Skill 的内部内容复制进来。

## 12. 完成前去重 / 越界自检

每次 Skill 编写或修改完成前，至少检查：

```text
1. 我是否写了其他环节“应该怎么做”？
2. 我是否复制或改写了另一个 owner 已经定义的规则？
3. 是否存在一条规则以后修改时必须同步更新多个文件？
4. 当前外部内容能否缩成 consume / require / handoff，而不是重新描述其内部实现？
```

任一答案为“是”时，先处理 ownership/去重问题，再认为当前 Skill 可以交付。

## 13. 拆分/重复警告

出现以下情况时必须检查并重构：

- 同一规则在两个文件完整出现；
- 当前 Skill 开始替另一个 Skill 定义内部行为；
- main Skill 与 supporting Skill 重复同一流程；
- validation 为了分类被无必要单独拆出；
- 主流程被 schema、字段表或 parser 中间层淹没；
- reference 重新描述 `SKILL.md` 完整流程；
- 修改一个定义必须同步多个 owner；
- 新 Skill 为兼容 Legacy Runtime 又复制 route/task/result/event 接口；
- 新 Skill 仅因为旧目录结构而被强行分类。
