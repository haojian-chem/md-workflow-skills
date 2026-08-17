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

不要先按 Workflow / Operation / Validator 分类再决定文件结构，也不要为了“完整”自动生成空目录、空 schema 或配套 Validator。

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
读取当前 authority + 目标 Skill + 直接相关上下游/相邻 Skill
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
处理被本次改动取代的旧 Markdown
↓
更新 current index/content map
```

不得先批量生成一套目录/模板，再把实际职责硬塞进去。

## 5. 过期 Markdown 归档

当前 authoring/Skill 活跃路径中不应长期保留 `SUPERSEDED` / `LEGACY` / `HISTORY ONLY` Markdown tombstone。

当一个 `.md` 已明确被当前文件取代，且不再是 runtime/authoring authority 时：

1. 确认 current 文件已经完整接管其仍有效内容；
2. 更新所有 current 引用，使普通 authoring/runtime 不再依赖旧路径；
3. 将需要保留以便历史查阅的 Markdown 移入：

```text
00_authoring/archive/
```

4. archive 尽量保留原来的相对语义，例如：

```text
00_authoring/archive/
└── md-workflow-skill-authoring/
    ├── references/
    └── assets/
```

5. 从原 active path 删除旧 Markdown；不要同时在 active path 留一份 tombstone、archive 再留一份副本；
6. Git history 继续保存完整历史版本。

Archive 文件不是 current authority，普通 Skill authoring、Task Execution Agent 和 Manager 均不得默认读取。

## 6. 什么不应归档

不要因为“文件较旧”就归档仍然有效的：

- current `SKILL.md`；
- current references；
- 仍然有效的 architecture-freeze record；
- current template/index/status file；
- 真实科研项目的结果或运行记录。

归档依据是**authority 已被明确取代**，不是文件日期。

## 7. 替换检查

当新文件替换旧文件时，交付前确认：

- [ ] 新 main Skill / reference 已接管所有仍有效规则；
- [ ] current 文件不再引用旧路径；
- [ ] 同一规则没有在新旧文件各保留一份；
- [ ] 旧 Markdown 已归档或删除，而不是继续留在 active 搜索路径；
- [ ] archive 没有被加入默认 startup/read list；
- [ ] content map / inventory 只指向 current authority。

## 8. 原则摘要

```text
一个职责 → 一个 main Skill
长而同属当前职责 → reference
复杂且独立 → supporting Skill
确定性机械能力 → script / Tool
已被取代的 Markdown → archive，不留在 active path
已有 owner 的规则 → 引用，不复制
```
