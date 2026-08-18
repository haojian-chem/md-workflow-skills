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

- 对应 Stage / Step 的 `architecture_freezes/`；
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

Scientific roots 按 MD Workflow Stage 固定为：

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

这些 Stage / Step 目录可以在正式 `SKILL.md` 生成前预先保留，用于稳定规划路径和后续 Skill package 落位；**目录存在不等于 Skill 已生成或已激活**。

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

**Architecture freeze 完成不等于 Skill generation 已获许可。** 只有用户明确要求生成/实现某个 Skill 时，才把对应 freeze 转写为 active `SKILL.md`。

# Authoring status maintenance

`project_design/MD_WORKFLOW_MASTER_PLAN.md` 是项目级 **Stage / Step 建设状态与 current entry 的唯一状态 owner**。既然维护这个状态文件，任何真正改变实现状态的 authoring 工作都必须同步它；不能把状态维护留给“以后某个窗口顺手更新”。

以下变化都属于必须同步的状态变化：

```text
讨论/设计中
→ architecture frozen

architecture frozen
→ Skill generation approved / in progress

freeze-only
→ active SKILL.md generated

active Skill
→ representative validation completed / implementation milestone changed

current Skill / freeze
→ superseded / retired / replaced
```

对于正式 Skill generation，交付顺序固定为：

```text
读取 current main + 对应 freeze + authoring rules
↓
生成 / 修改目标 Skill package
↓
完成本次要求的 validation / self-check
↓
更新直接拥有该入口的 Stage main Skill（如果它维护 current/freeze-only entry）
↓
同步 MD_WORKFLOW_MASTER_PLAN.md 中对应 Stage / Step 的状态与 current entry
↓
如新增/替换 freeze，再同步 architecture_freezes/README.md
↓
交付
```

因此：**目标 `SKILL.md` 写完但状态 owner 尚未同步，不算完整交付。**

多窗口时采用窄范围状态同步：

- authoring 窗口在写状态前必须重新读取 current `main` 和 `coordination/file_ownership.yaml`；
- 若 `MD_WORKFLOW_MASTER_PLAN.md` 没有被其他窗口显式占用，完成 Skill 的窗口可以只修改与自己 Stage / Step 对应的状态/current-entry 行，不获得修改其他 Stage catalog/architecture 的权限；
- 若该共享文件已有显式 writer，占用窗口不得并发写；必须把精确的状态变更交给当前 writer，并在交付中明确“状态同步待 owner 落地”，不能静默跳过；
- 不为解决状态同步再建立 parallel `status.yaml`、skill inventory 或第二份 sync 文档。

# Main Skill boundary

main Skill 应让 Agent 能确定：

```text
目标
输入 / 对象 / 证据
reuse 条件
科学 / 技术边界
执行 / 判断方式
validation
results
何时读取额外 reference / supporting Skill / Tool
```

这些是信息要求，不是固定 section schema，也不表示所有运行时判断都必须预先固化成 Skill 规则。

“不做什么”只在有实际边界价值时明确：例如防止高概率越界/误操作、保护数据或不可逆操作、阻止已明确否定的常见默认行为，或直接影响 validation/result correctness。不要为了“范围完整”罗列所有本 Skill 不负责的事项。

详细边界：`references/skill_boundaries.md`。

# Rule necessity gate

在判断一条规则归谁拥有之前，先判断它**是否有必要成为 Skill 的固定规则**。

Skill 优先固定需要跨任务保持一致、且对当前职责正确性有实际价值的内容，例如：稳定科学/技术判据、输入/输出接口、reuse 与 validation 语义、安全或数据完整性边界、正式结果生命周期，以及不固定就会高概率造成越界或歧义的约束。

如果某项决定可以由 Task Execution Agent 或用户根据当前任务上下文可靠判断，且不需要形成跨任务稳定语义、接口约束、科学判据或结果生命周期，则保留为运行时裁量；**不要因为“运行时可能遇到这种情况”就继续把它固化成统一决策树、状态转换规则、fallback 链或完整工作流。**

前置 gate：

```text
这件事必须写成 Skill 固定规则吗？
├─ 是：缺少固定规则会影响跨任务一致性、科学/技术正确性、接口/结果语义、安全或高概率边界执行
│  → 继续 rule-ownership gate
└─ 否：Agent / 用户可基于当前任务可靠判断
   → 保留运行时裁量，不继续下钻为 Skill 规则
```

# Ownership and deduplication

向当前 Skill 增加规则前，按需读取 `references/content_ownership_and_deduplication.md`。

通过 rule-necessity gate 后，再执行 ownership gate：

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

状态同步是唯一的窄共享写例外，只允许修改当前 authoring 工作直接造成的对应状态/current-entry，不扩展科学内容 ownership。

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

正式结果必须让后续执行能够定位并理解，而不要求重读上游全过程。

# Architecture freezes and archive

Stage / Workflow / pre-Skill Step architecture freeze：`architecture_freezes/`。

历史 authoring/design Markdown：`archive/`。

Legacy executable/runtime material：`../legacy/`。

`archive/` 与 `legacy/` 均不是 ordinary startup/read list。

# Delivery check

- [ ] main Skill 能直接指导 Agent 完成当前职责；
- [ ] 未把可由 Agent / 用户按当前任务可靠判断的策略，无必要地固化成决策树、状态机、fallback 链或完整工作流；
- [ ] 长/条件性细节没有在 main Skill 与 reference 重复；
- [ ] supporting Skill 拆分有真实复杂度和边界价值；
- [ ] 未建立不必要 parser/wrapper/dispatcher；
- [ ] 未重新定义其他 owner 的内部规则；
- [ ] 未为“范围完整”罗列无实际必要的 negative-scope 清单；
- [ ] current scientific root 与 Stage 编号一致；
- [ ] 预留 Step 目录没有被误写成“Skill 已生成”；
- [ ] evals/tools/legacy 未被误当成 Stage Skill；
- [ ] reuse、validation、results 足以支持跨对话继续；
- [ ] 若本次改变了 freeze / Skill / validation 建设状态，`MD_WORKFLOW_MASTER_PLAN.md` 已同步，或存在明确且未完成的 writer handoff；
- [ ] 若 Stage main Skill 维护 current/freeze-only entry，其入口状态已同步；
- [ ] 未重新引入 Legacy Workstream/route/event/transaction runtime。
