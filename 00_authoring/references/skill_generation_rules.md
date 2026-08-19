# Skill generation and Markdown archival rules

Status: CURRENT

本文件定义新建、重构和冻结科研 Skill 时的默认生成方式、状态同步要求，以及过期 Markdown 的归档规则。

## 1. 默认生成模型与目录保留

科研 Skill 默认从一个 main `SKILL.md` 开始：

```text
<skill-directory>/
├── SKILL.md
├── references/        # optional
├── schemas/           # optional
├── scripts/           # optional
└── <supporting-skill>/SKILL.md   # only when justified
```

正式 Skill package 中只有 `SKILL.md` 是默认必需业务文件。其他目录只有在当前职责确实需要时才创建。

但 **Stage / Step 目录身份与 `SKILL.md` 激活状态是两件事**。如果某个 Stage / Step 的编号、名称和未来 package 路径已经确定，可以在正式 Skill generation 前保留该目录。Git 需要占位文件时使用最小 `.gitkeep`；不要为了保留目录创建伪 `README`、空 schema 或伪 `SKILL.md`。

因此：

```text
目录存在
≠ Skill 已生成
≠ Skill 已激活

SKILL.md 存在且已按许可生成
→ 才表示该 Step 有 active Skill entry
```

撤回未经许可的伪 `SKILL.md` 时，如果目录规划本身正确，**删除伪 Skill 文件但保留目录**；不要把正确的 Stage / Step 目录一起删掉。

不要先按 Workflow / Operation / Validator 分类再决定文件结构，也不要为了“完整”自动生成空 schema、content map 或配套 Validator。

## 2. Main Skill 与 references

main `SKILL.md` 保存 Agent 执行当前职责所需的主线：

- purpose / scope；
- 当前输入、对象和证据；
- reuse；
- 核心执行/判断边界；
- validation；
- results；
- 何时按需读取 reference、调用 supporting Skill 或 Tool。

属于当前 Skill、但过长或只在特定条件下需要的内容优先放 `references/`，例如：

- 长科学规则；
- registry / table；
- 大枚举；
- 复杂选择规则；
- 特定对象才需要的方法细节。

主 Skill 对 reference 只保留：

```text
何时读取
→ 读取哪个 reference
→ 它解决什么局部问题
```

不要在 main Skill 和 reference 中各写一份完整规则。某条详细规则一旦下放给 reference，reference 是该细节的 owner，main Skill 只保留必要摘要和入口。

### Negative scope / 禁止项

“不做什么”不是 main Skill 的默认完整性要求。不要为了显得职责边界完整，系统性罗列所有相邻环节、下游环节或理论上可能发生但当前 Skill 不负责的事项。

只有在以下情况之一成立时，才应明确写出 `不做 / 不得 / 禁止`：

- 容易与当前职责混淆，不明确会高概率导致实际越界或误操作；
- 用于保护当前 Skill 的 ownership，阻止其承担其他 owner 的职责；
- 属于安全、数据完整性、不可逆操作或输入保护边界；
- 是当前设计中已明确否定、且 Agent 很可能采用的默认行为；
- 对 validation 或 result correctness 有直接影响。

若上述必要性不存在，则不需要出现对应 negative-scope 条目。未被列出的外部职责自然由当前 Skill 的 purpose / scope、ownership 和 external-skill boundary 限制；不要通过冗长的“本 Skill 不负责……”清单重复描述其它环节。

### Rule necessity gate

在对拟新增内容执行 ownership 判断之前，先判断它是否真的需要成为 Skill 的固定规则。

Skill 应优先固定需要跨任务保持一致、且对职责正确性有实际价值的内容，例如：

- 稳定的科学/技术判据；
- 输入/输出接口和依赖语义；
- reuse / validation / formal-result 语义；
- 安全、数据完整性或不可逆操作边界；
- 不固定就会高概率造成越界、歧义或不可恢复结果的约束。

以下本身**不足以**构成规则化理由：

- 运行时可能遇到某种异常或分支；
- 为了让流程看起来完整；
- 可以继续细分出更多状态转换；
- Agent 将来“可能需要知道怎么选”。

如果某项决定可以由 Task Execution Agent 或用户根据当前上下文可靠判断，且不要求形成跨任务稳定语义、接口约束、科学判据或结果生命周期，则保留为运行时裁量，不继续把它展开成统一 decision tree、状态机、fallback 链或完整工作流。

判断顺序：

```text
这件事必须成为 Skill 固定规则吗？
├─ 否 → 留给 Agent / 用户按当前任务判断；停止规则下钻
└─ 是 → 再判断该规则归谁拥有
```

因此 **rule-necessity gate 必须先于 rule-ownership gate**。一条内容即使“没有其它 owner”，也不自动意味着当前 Skill 应该把它规则化。

## 3. Supporting Skill 的拆分门槛

只有内容同时具备明显复杂度和清楚独立边界时才拆 supporting Skill，例如：

- 可独立按需加载；
- 有独立完整科学/技术职责；
- 被多个 main Skill 复用；
- 需要独立测试/validation 生命周期；
- 拆分能显著降低主 Skill 上下文，而不会增加无意义 dispatcher hop。

如果只是“内容比较长”，优先 reference；如果只是几条 validation 或 helper 规则，不单独拆 Skill。

## 4. 生成顺序

新建或重构 Skill 时按以下顺序：

```text
读取 00_authoring/SKILL.md + 当前目标 Skill / 对应 freeze + 直接相关上下游/相邻 Skill
↓
读取 MD_WORKFLOW_MASTER_PLAN.md 中目标 Stage / Step 的当前建设状态
↓
确认当前 Skill 的唯一职责与 write ownership
↓
对拟新增内容先执行 rule-necessity gate
↓
只对确有必要固定的规则执行 rule-ownership gate
↓
先完成 main SKILL.md 主线
↓
识别长/条件性细节 → references/
↓
仅在复杂且边界清晰时拆 supporting Skill
↓
仅在确有机器约束/确定性能力时增加 schemas/scripts/Tool
↓
检查越界定义、重复定义、shadow specification，以及是否把 Agent/用户的任务级裁量误固化成流程
↓
完成本次要求的 validation / self-check
↓
处理被本次改动取代的旧文件，但保留仍正确的 Stage / Step 目录
↓
同步 Stage main Skill 的 current/freeze-only entry（如该 Stage main Skill维护入口）
↓
同步 MD_WORKFLOW_MASTER_PLAN.md 中目标 Stage / Step 的建设状态与 current entry
↓
如新增/替换 architecture freeze，再同步 architecture_freezes/README.md
↓
交付
```

不得先批量生成一套目录、YAML metadata 或模板，再把实际职责硬塞进去。

**Architecture freeze 完成不等于 Skill generation 已获许可。** 只有用户明确要求生成/实现某个 Skill 时，才把对应 freeze 转写为 active `SKILL.md`。

## 5. Architecture-freeze 文件位置与粒度

当某个 Stage / Workflow / Step 的设计已经明确敲定，需要保存正式 freeze record 时，统一写入：

```text
00_authoring/architecture_freezes/
```

规则：

- 不在 `00_authoring/` 根目录散放新的 `WORKFLOW*_ARCHITECTURE_FREEZE*.md`；
- freeze 可以是 Stage-level，也可以是尚未正式生成 Skill 的 Step-level；
- freeze 保存已经冻结的架构、职责边界、关键科学/技术规则和明确拒绝项；
- 当目标 Step **尚无 current Skill** 时，freeze 可以保留已经讨论到 implementation-ready 的细节，作为后续 Skill generation 的直接输入，避免重复讨论或信息丢失；
- freeze 文件不是 runtime Skill，不能因为内容足够详细就作为 `SKILL.md` 直接执行；
- 当正式 current Skill 已经生成后，具体可变执行细节由对应 current `SKILL.md` / references 拥有；freeze 不维护第二套平行的 mutable specification；
- 如果 Skill generation 发现此前讨论已经明确但 freeze 漏记的事实，应先补回对应 freeze 或在同次 authoring 中明确归属，不从历史伪 Skill 中静默丢失；
- 同一 Stage / Step 有新的 freeze record 明确取代旧 freeze 时，先迁移 current 引用，再将被取代的旧 Markdown 移入 `00_authoring/archive/`；
- `00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 只记录 current freeze 入口和建设状态，不复制完整 freeze 内容。

当前目录入口：

`00_authoring/architecture_freezes/README.md`

## 6. 状态维护是生成流程的一部分

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md` 是项目级 Stage / Step **建设状态与 current entry 的唯一 owner**。

它不是静态说明文件。只要 authoring 工作改变了真实状态，就必须在同一工作流中同步；否则状态文件会失去意义。

必须同步的典型变化包括：

```text
设计中 → FROZEN
freeze-only → Skill generation approved / in progress
freeze-only → active Skill generated
active Skill → representative validation milestone changed
current → superseded / retired / replaced
```

### 6.1 Skill generation 的完成条件

生成目标 `SKILL.md` 后，至少检查：

1. `MD_WORKFLOW_MASTER_PLAN.md` 中该 Step 是否仍写成 `freeze-only / under authoring / not generated`；
2. 对应 Stage main Skill 是否仍把该 Step 指向 freeze 而不是 current `SKILL.md`；
3. 是否新增或替换了 architecture freeze，需要更新 `architecture_freezes/README.md`；
4. 是否改变了 Stage 总体状态描述。

只要其中存在需要更新的项，就必须一起修改。

**`SKILL.md` 已写入但这些状态入口仍陈旧，不算完整 Skill generation。**

### 6.2 多窗口状态同步

状态同步不得因为 `MD_WORKFLOW_MASTER_PLAN.md` 是共享文件而被静默跳过。

规则：

- 写状态前重新读取 current `main` 和 `coordination/file_ownership.yaml`；
- 若 Master Plan 没有被其他窗口显式占用，完成当前 Skill 的窗口拥有一个**窄的 status-only 写权限**：只改自己 Stage / Step 的建设状态与 current entry；
- 这个例外不授予修改其他 Stage catalog、architecture 或科学规则的权限；
- 若 Master Plan 已有显式 writer，则不并发写，向该 writer 提交精确的状态变更；交付时必须明确该同步仍待落地，不能宣称 repository integration 已全部完成；
- 不建立新的 `SYNC_STATUS.md`、`status.yaml`、skill inventory 或其他 parallel 状态层。

## 7. Project-design 与 runtime 的位置

项目级 authoring 设计资料位于：

```text
00_authoring/project_design/
```

当前其中只承担 project-level design / status 的文件：

```text
MD_WORKFLOW_MASTER_PLAN.md
→ Stage numbering / catalog / 建设状态 / current entry
```

跨 Stage Task Execution runtime **不属于 authoring project-design Markdown**。其 current runtime owner 是：

```text
00_runtime/SKILL.md
```

Authoring 在涉及跨 Stage runtime 边界时读取该 runtime Skill，但不得在 `project_design/` 再维护第二份 runtime specification。

不要把具体 Stage 的内部科学规则、字段、validation 或文件生命周期复制进 project-design 文档；这些内容继续由对应 current Skill / reference / architecture freeze 拥有。

不再单独维护 current `SYNC_STATUS.md`。如果某项内容只是“当前 Stage 建设到哪里”，归入 Master Plan；如果是具体规则，则归入真正的规则 owner。

## 8. 过期文件归档

当前 authoring/Skill 活跃路径中不应长期保留 `SUPERSEDED` / `LEGACY` / `HISTORY ONLY` 文件作为伪 current entry。

当一个文件已明确被 current authority 取代，且不再是 runtime/authoring authority 时：

1. 确认 current 文件已经完整接管其仍有效内容；
2. 更新所有 current 引用，使普通 authoring/runtime 不再依赖旧路径；
3. 需要保留以便历史查阅的 Markdown 移入：

```text
00_authoring/archive/
```

4. archive 按语义归类，例如 `root_history/`、`legacy_runtime/`、旧 authoring assets；
5. 从原 active path 删除旧文件；不要同时在 active path 留 tombstone、archive 再留一份副本；
6. 对不再有 current 用途的旧 YAML/schema/index，通常直接从 active path 删除，由 Git history 保留历史；只有明确有审计价值时才归档；
7. Git history 继续保存完整历史版本。

如果被撤回的是**未经许可的伪 Skill implementation**，先把已经讨论并敲定、仍有后续生成价值的信息完整迁入对应 architecture freeze；再删除伪 `SKILL.md`。若其 Stage / Step 目录规划仍然正确，则保留该目录，不按“旧文件归档”规则把目录整体移走。

Archive 文件不是 current authority，普通 Skill authoring、Task Execution Agent 和 Manager 均不得默认读取。

## 9. 什么不应归档

不要因为“文件较旧”就归档仍然有效的：

- current `SKILL.md`；
- current references；
- 仍然有效的 architecture-freeze record；
- 已确定、仍用于未来 Skill 落位的 Stage / Step package 目录；
- 当前确有独立用途的 template / coordination record / project-design document；
- 真实科研项目的结果或运行记录。

归档依据是**authority 已被明确取代**，不是文件日期。

## 10. Metadata 最小化

不要默认给每个 Skill 再创建一份平行 metadata 来描述它自己已经说明的内容。

当前默认不建立：

```text
content map
skill inventory entry
额外 role taxonomy YAML
```

如果某个结构化文件没有独立机器用途，只是在重复：

```text
Skill 在哪里
Skill 拥有什么
Skill 引用了谁
Skill 当前是什么状态
```

则优先删除这层 metadata，由实际 `SKILL.md`、目录结构以及真正独立的 Stage/Tool/coordination 记录承担各自职责。

## 11. 替换 / 生成检查

交付前确认：

- [ ] 新 main Skill / reference / freeze 已接管所有仍有效规则；
- [ ] current 文件不再引用错误旧路径；
- [ ] 同一规则没有在新旧 active 文件各保留一份；
- [ ] 没有把可由 Agent / 用户基于当前任务可靠判断的策略，继续展开成无必要的统一决策树、状态机、fallback 链或完整工作流；
- [ ] 被撤回的伪 Skill 已删除，但正确的 Stage / Step 目录仍保留；
- [ ] archive 没有被加入默认 startup/read list；
- [ ] architecture-freeze 使用 `00_authoring/architecture_freezes/` current 路径；
- [ ] freeze 与 Skill 的授权状态没有混淆：freeze-only 不能被当作 active runtime Skill；
- [ ] 如果本次改变了建设状态，`MD_WORKFLOW_MASTER_PLAN.md` 已同步或有明确 writer handoff；
- [ ] Stage main Skill 中对应 current/freeze-only entry 已同步；
- [ ] project-level 状态只在 Master Plan 维护，不再另建 parallel sync/status 文件；
- [ ] 没有为了 discoverability 又建立一份重复 Skill 内容的 YAML metadata。

## 12. 原则摘要

```text
一个职责 → 一个 main Skill
长而同属当前职责 → reference
复杂且独立 → supporting Skill
确定性机械能力 → script / Tool
可由 Agent / 用户基于当前任务可靠判断、无需跨任务稳定的策略 → 不固化为 Skill 规则
已确定 Stage / Step package 路径 → 可先保留目录；目录存在 ≠ Skill 已生成
Stage / Workflow / pre-Skill Step architecture freeze → 00_authoring/architecture_freezes/
freeze 完成 ≠ Skill generation 获批
Skill generation 改变状态 → 必须同步 MD_WORKFLOW_MASTER_PLAN.md
跨 Stage Task Execution runtime → 00_runtime/SKILL.md
项目级 authoring design / status → 00_authoring/project_design/
多窗口 writer assignment → 00_authoring/coordination/
已被取代的 Markdown → archive
无独立用途的旧 YAML/schema/index → 删除 active copy，Git history 保留
已有 owner 的规则 → 引用，不复制
```