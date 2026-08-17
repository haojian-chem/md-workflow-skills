---
name: md-workflow-skill-authoring
description: 设计、编写、冻结、审查或重构本项目科研 Skill 时使用。以 main Skill 指导 Agent 完成职责为核心；长/条件性细节进入 references，只有复杂且边界清晰时拆 supporting Skill；严格避免跨 Skill 越权定义、重复定义、无必要 parser/workflow gate 和过期文件留在 active path。
---

# Purpose

本文件是 `00_authoring/` 的**唯一 Skill authoring 主入口**。

Skill 的目标是指导 Agent 如何处理科研任务，不是把 Agent 锁进固定 parser、schema、wrapper、dispatcher 或人为 workflow engine。

默认关系：

```text
Manager
→ Task Sheet
→ Task Execution Agent
→ 当前科研 main Skill
   ├─ 按需读取 references
   ├─ 必要时调用 supporting Skill
   └─ 必要时调用 deterministic Tool
```

# New-window startup

新开的 Skill authoring / maintenance 窗口默认先读取：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

然后按当前任务需要读取：

- 对应 Stage 的 `architecture_freezes/`；
- 与当前输入、输出或科学边界直接相关的上下游 / 相邻 Skill；
- 当前 Skill 明确需要的 reference / Tool guide；
- 项目级阶段目录 / 建设状态需要时读 `project_design/MD_WORKFLOW_MASTER_PLAN.md`；
- 跨 Stage runtime architecture 需要时读 `project_design/lightweight_runtime_v2_spec.md`；
- 多窗口写入协调需要时读 `coordination/file_ownership.yaml` 或 work order。

不要启动时预加载整个 `00_authoring/`。

提出或实施修改前恢复当前讨论状态：

```text
已做过
已否定
仍未验证
```

没有新证据改变前提时，不重复已经明确否定的方案。

# Skill generation

详细生成规则按需读取：

`references/skill_generation_rules.md`

默认模型：

```text
一个职责
→ 一个 main SKILL.md
→ 长且仍属于当前职责的内容放 references/
→ 只有复杂且独立时拆 supporting Skill
→ 只有确有稳定机器约束 / 确定性能力时增加 schemas / scripts / Tool
```

当前 active scientific Skill 按 Stage / 科学职责组织，例如：

```text
01_structure_preparation/
02_topology_preparation/
04_md_simulation/
05_analysis/
```

历史 Workflow / Operation / Validator role-based roots 已退出 active scientific Skill layout；不得为新 Skill 恢复这套分类，也不保留 compatibility copy。

普通科研 Skill 模板：`assets/skill.template.md`。
Manager 模板：`assets/manager_skill.template.md`。

# Main Skill boundary

main Skill 应足够让 Agent 回答：

```text
当前目标是什么？
处理哪些输入 / 对象 / 证据？
什么情况下可以复用已有结果？
有哪些必须遵守的科学 / 技术边界？
如何执行或判断？
怎样确认结果有效？
哪些结果和记录需要交接？
何时需要额外 reference / supporting Skill / Tool？
```

这些是信息要求，不是固定 section schema。

详细边界：`references/skill_boundaries.md`。

# Rule ownership and deduplication

向当前 Skill 加科学、执行、validation、结果或文件生命周期规则前，按需读取：

`references/content_ownership_and_deduplication.md`

核心判断：

```text
这条规则属于当前 Skill 自己？
├─ 是 → 当前 Skill 定义
└─ 否
   ↓
   外部已有 owner？
   ├─ 有 → 只引用，不复制 / 改写成第二份规范
   └─ 没有或有冲突 → 提 cross-skill finding
```

当前 Skill 可以定义“我需要外部 Skill 提供什么”，不能定义“外部 Skill 应该怎样把它做出来”。

禁止 shadow specification。

# Read broadly, write narrowly

```text
read scope 可以宽
write ownership 必须窄
```

业务窗口可以并且应该读取直接相关的上下游 / 相邻 Skill，以理解接口、避免重复和确认 handoff；读取不代表获得修改权或定义权。

对外部 Skill 只记录必要的 `consume / require / handoff`。发现外部问题时提交 finding，不在当前 Skill 偷偷补一份外部规则。

详细协议：`references/multi_window_authoring_protocol.md`。

显式多窗口 assignment 使用：

```text
coordination/file_ownership.yaml
coordination/window_work_orders/
```

# References and supporting Skills

属于当前 Skill、但过长或只在特定条件下需要的内容优先放 `references/`。

main Skill 只保留“何时读取 → 哪个 reference → 解决什么局部问题”，不要和 reference 各维护一份完整规则。

Supporting Skill 只有内容复杂、可独立加载、边界稳定且独立维护确有价值时才拆分；不要为了 validation 配对、目录对称或减少几段文字增加 Skill hop。

渐进披露：`references/progressive_disclosure.md`。

# Tool boundary

Tool 是确定性能力组件，不是 Agent 理解任务的许可层。

适合 Tool 的内容包括精确 parsing、hash / mapping、批量结构化提取、稳定文件变换、格式校验和高重复度确定性计算。

如果 Agent 可以可靠直接读取输入并完成开放式科学判断，不要仅因为已有 parser / Tool 就规定必须先经过它。

详细规则：`references/deterministic_tool_protocol.md`。

共享 Tool 的开发与生命周期由 `md-workflow-tool-authoring/SKILL.md` 负责。

# Reuse, validation and results

当前 Skill 应定义真正影响本职责结果是否有效 / 可复用的条件，不根据文件名或目录存在猜测。

通常：

```text
明确等价 → 自动复用
明确不等价 → 重新执行
信息不足 → 当前 Task Execution Agent 向用户确认
用户明确要求重做 / 对照 → 不自动复用
```

Validation 默认跟随当前结果 owner；只有复杂且边界清晰时才拆 supporting validation Skill。

正式结果与 handoff 必须让下游能够定位并理解，不要求下游重新读取上游全过程。

# Architecture freezes and archive

Stage / Workflow architecture freeze 统一放在 `architecture_freezes/`。

被 current authority 明确取代的历史 Markdown 移入 `archive/`；active path 不留同名 / 同义 tombstone。

详细规则：`references/skill_generation_rules.md`。

# Project-level support

以下是按需辅助材料，不高于本 `SKILL.md`：

```text
project_design/MD_WORKFLOW_MASTER_PLAN.md
project_design/lightweight_runtime_v2_spec.md
architecture_freezes/
coordination/
```

不再为每个 Skill 维护平行的 content-map / skill-inventory 元数据。

# Delivery check

提交前至少确认：

- [ ] main Skill 能直接指导 Agent 完成当前职责；
- [ ] 长 / 条件性细节使用 reference，而不是重复写两份；
- [ ] supporting Skill 只在复杂且边界清晰时存在；
- [ ] 未把 Agent 锁死到不必要 parser / wrapper / dispatcher；
- [ ] 未重新定义其他 Skill 的内部规则；
- [ ] 已有 owner 的规则只引用，没有 shadow specification；
- [ ] 已按需读取相关上下游 Skill，但没有越过 write ownership；
- [ ] reuse、validation、results / handoff 足以支持跨对话继续；
- [ ] 本次产生的过期 Markdown 已归档，不再留在 active path；
- [ ] 没有重新引入 Legacy Workstream / route / event / transaction runtime。

Authoring 对话交付只报告本窗口修改、validation、cross-skill findings 和未决问题，不复制其他 Skill 的内部设计。
