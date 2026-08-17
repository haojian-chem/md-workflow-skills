# Skill generation and Markdown archival rules

Status: CURRENT

本文件定义新建、重构和冻结科研 Skill 时的默认生成方式，以及过期 Markdown 的归档规则。

## 1. 默认生成模型

科研 Skill 默认从一个 main `SKILL.md` 开始：

```text
<skill-directory>/
├── SKILL.md
├── references/        # optional
├── schemas/           # optional
├── scripts/           # optional
└── <supporting-skill>/SKILL.md   # only when justified
```

只有 `SKILL.md` 是默认必需文件。其他目录只有在当前职责确实需要时才创建。

不要先按 Workflow / Operation / Validator 分类再决定文件结构，也不要为了“完整”自动生成空目录、空 schema、content map 或配套 Validator。

## 2. Main Skill 与 references

main `SKILL.md` 保存 Agent 执行当前职责所需的主线：

- purpose / scope；
- 当前输入、对象和证据；
- reuse；
- 核心执行/判断边界；
- validation；
- results / handoff；
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
确认当前 Skill 的唯一职责与 write ownership
↓
对拟新增规则执行 rule-ownership gate
↓
先完成 main SKILL.md 主线
↓
识别长/条件性细节 → references/
↓
仅在复杂且边界清晰时拆 supporting Skill
↓
仅在确有机器约束/确定性能力时增加 schemas/scripts/Tool
↓
检查越界定义、重复定义和 shadow specification
↓
处理被本次改动取代的旧文件
↓
按需要更新 Stage/Step freeze / Master Plan / Tool registry / coordination record 等真正有独立职责的共享入口
```

不得先批量生成一套目录、YAML metadata 或模板，再把实际职责硬塞进去。

**Architecture freeze 完成不等于 Skill generation 已获许可。** 只有用户明确要求生成/实现某个 Skill 时，才把 freeze 转写为 active `SKILL.md`。

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

## 6. Project-design 文档

项目级设计资料统一位于：

```text
00_authoring/project_design/
```

当前职责分工：

```text
MD_WORKFLOW_MASTER_PLAN.md
→ Stage numbering / catalog / 建设状态 / current entry

lightweight_runtime_v2_spec.md
→ 跨 Stage Lightweight Runtime 通用架构
```

不要把具体 Stage 的内部科学规则、字段、validation 或文件生命周期复制进 project-design 文档；这些内容继续由对应 current Skill / reference / architecture freeze 拥有。

不再单独维护 current `SYNC_STATUS.md`。如果某项内容只是“当前 Stage 建设到哪里”，归入 Master Plan；如果是具体规则，则归入真正的规则 owner。

## 7. 过期文件归档

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

Archive 文件不是 current authority，普通 Skill authoring、Task Execution Agent 和 Manager 均不得默认读取。

## 8. 什么不应归档

不要因为“文件较旧”就归档仍然有效的：

- current `SKILL.md`；
- current references；
- 仍然有效的 architecture-freeze record；
- 当前确有独立用途的 template / coordination record / project-design document；
- 真实科研项目的结果或运行记录。

归档依据是**authority 已被明确取代**，不是文件日期。

## 9. Metadata 最小化

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

## 10. 替换检查

当新文件替换旧文件时，交付前确认：

- [ ] 新 main Skill / reference / freeze 已接管所有仍有效规则；
- [ ] current 文件不再引用旧路径；
- [ ] 同一规则没有在新旧 active 文件各保留一份；
- [ ] 旧文件已归档或删除，而不是继续留在 active 搜索路径；
- [ ] archive 没有被加入默认 startup/read list；
- [ ] architecture-freeze 使用 `00_authoring/architecture_freezes/` current 路径；
- [ ] freeze 与 Skill 的授权状态没有混淆：freeze-only 不能被当作 active runtime Skill；
- [ ] project-level 状态只在 Master Plan 维护，不再另建 parallel sync/status 文件；
- [ ] 没有为了 discoverability 又建立一份重复 Skill 内容的 YAML metadata。

## 11. 原则摘要

```text
一个职责 → 一个 main Skill
长而同属当前职责 → reference
复杂且独立 → supporting Skill
确定性机械能力 → script / Tool
Stage / Workflow / pre-Skill Step architecture freeze → 00_authoring/architecture_freezes/
freeze 完成 ≠ Skill generation 获批
跨 Stage project design → 00_authoring/project_design/
多窗口 writer assignment → 00_authoring/coordination/
已被取代的 Markdown → archive
无独立用途的旧 YAML/schema/index → 删除 active copy，Git history 保留
已有 owner 的规则 → 引用，不复制
```
