---
name: md-workflow-skill-authoring
description: 设计、编写、冻结、审查或重构本项目科研 Skill 时使用。以 main Skill 指导 Agent 完成职责为核心；长/条件性细节进入 references，只有复杂且边界清晰时拆 supporting Skill；避免跨 Skill 越权、重复定义、无必要 parser/workflow gate 和过期文件留在 active path。
---

# Purpose

本文件是 `00_authoring/` 的唯一 Skill authoring 主入口。

Skill 的目标是指导 Agent 处理科研任务，而不是把 Agent 锁进固定 parser、schema、wrapper、dispatcher 或人为 workflow engine。

默认关系：

```text
Manager
→ Task Sheet
→ Task Execution Agent
→ 当前科研 main Skill
   ├─ 按需 references
   ├─ 必要时 supporting Skill
   └─ 必要时 deterministic Tool
```

# New-window startup

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

之后只按任务需要读取：

- 对应 Stage 的 `architecture_freezes/`；
- 与当前输入/输出/边界直接相关的相邻 Skill；
- 当前 Skill 明确需要的 reference / Tool guide；
- 项目级 Stage catalog/status 需要时读 `project_design/MD_WORKFLOW_MASTER_PLAN.md`；
- 跨 Stage runtime 需要时读 `project_design/lightweight_runtime_v2_spec.md`；
- 多窗口写入协调需要时读 `coordination/`。

提出或实施迭代修改前恢复：

```text
已做过
已否定
仍未验证
```

没有新证据改变前提时，不恢复已否定方案。

# Scientific Skill layout

Current active scientific roots：

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

这些编号只对应 MD Workflow Stage 1–5。

以下为 unnumbered repository infrastructure，不是 Scientific Skill root：

```text
evals/
tools/
legacy/
```

历史 Workflow / Operation / Validator role-based roots 已退出 current layout，不保留 compatibility copy。

# Skill generation

详细规则：`references/skill_generation_rules.md`。

默认模型：

```text
一个职责
→ 一个 main SKILL.md
→ 长且仍属于当前职责的内容放 references/
→ 只有复杂且独立时拆 supporting Skill
→ 只有确有机器约束/确定性能力时增加 schemas/scripts/Tool
```

普通模板：`assets/skill.template.md`。

# Main Skill boundary

main Skill 应让 Agent 能确定：

```text
目标
输入 / 对象 / 证据
reuse 条件
科学 / 技术边界
执行 / 判断方式
validation
results / handoff
何时读取额外 reference / supporting Skill / Tool
```

这些是信息要求，不是固定 section schema。

详细边界：`references/skill_boundaries.md`。

# Ownership and deduplication

向当前 Skill 增加规则前，按需读取 `references/content_ownership_and_deduplication.md`。

核心 gate：

```text
这条规则属于当前 Skill 自己？
├─ 是 → 当前 Skill 定义
└─ 否
   ↓
   外部已有 owner？
   ├─ 有 → 只引用 owner，不复制 / 改写成第二份规范
   └─ 没有或冲突 → 提 cross-skill finding
```

当前 Skill 可以定义“我需要外部 Skill 提供什么”，不能定义“外部 Skill 应该怎样把它做出来”。

# Read broadly, write narrowly

```text
read scope 可以宽
write ownership 必须窄
```

可以并且应该读取直接相关的上下游/相邻 Skill 来理解接口，但未经重新分配不得修改它们，也不得在当前 Skill 中创建 shadow specification。

详细协议：`references/multi_window_authoring_protocol.md`。

# References / supporting Skills

属于当前 Skill 但过长或条件性强的细节优先放 `references/`。

Supporting Skill 只有在内容复杂、可独立加载、边界稳定且独立维护有价值时才拆；不要为了 validation 配对、目录对称或角色分类增加 Skill hop。

# Tool boundary

Tool 是确定性能力组件，不是 Agent 理解任务的许可层。

适合 Tool：精确 parsing、hash/mapping、批量结构化提取、稳定文件变换、格式校验和高重复度确定性计算。

Current shared Tool root：`tools/`。

Tool authoring：`md-workflow-tool-authoring/SKILL.md`。

Legacy runtime-dependent tools 位于 `../legacy/tools/`，不得为了调用它们重新构造旧 Runtime。

# Reuse, validation and results

通常：

```text
明确等价 → 自动复用
明确不等价 → 重新执行
信息不足 → 当前 Task Execution Agent 向用户确认
用户明确要求重做/对照 → 不自动复用
```

Validation 默认跟随结果 owner；只有复杂且边界清晰时才拆 supporting validation Skill。

正式结果与 handoff 必须让下游能够定位并理解，而不要求重读上游全过程。

# Architecture freezes and archive

Stage / Workflow architecture freeze：`architecture_freezes/`。

历史 authoring/design Markdown：`archive/`。

Legacy executable/runtime material：`../legacy/`。

`archive/` 与 `legacy/` 均不是 ordinary startup/read list。

# Delivery check

- [ ] main Skill 能直接指导 Agent 完成当前职责；
- [ ] 长/条件性细节没有在 main Skill 与 reference 重复；
- [ ] supporting Skill 拆分有真实复杂度和边界价值；
- [ ] 未建立不必要 parser/wrapper/dispatcher；
- [ ] 未重新定义其他 owner 的内部规则；
- [ ] current scientific root 与 Stage 编号一致；
- [ ] evals/tools/legacy 未被误当成 Stage Skill；
- [ ] reuse、validation、results/handoff 足以支持跨对话继续；
- [ ] 未重新引入 Legacy Workstream/route/event/transaction runtime。
