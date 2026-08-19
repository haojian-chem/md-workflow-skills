# MD Workflow Project Instructions

## 1. Repository modes

本仓库同时用于真实 MD 项目运行和 Skill / Tool authoring。Skill repository 与真实 MD project root 必须区分。

真实 MD 项目默认运行链：

```text
Manager
→ Task Sheet
→ 00_runtime/SKILL.md
→ long-lived Task Execution Agent
→ current Stage / Step main Skill
→ 按需 references / supporting Skills / deterministic Tools
```

Manager 请求读取 `00_manager/SKILL.md`；Task Sheet 建立后，任务执行先读取 `00_runtime/SKILL.md`，再从目标 `Txxxx.md` 定位当前项并进入对应 current scientific Skill。普通执行不返回 Manager 调度。

Skill authoring / maintenance 默认启动链：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

之后只按当前任务需要读取 architecture freeze、相邻 Skill、project design、Tool guide 或 coordination records。

## 2. Scientific Stage roots

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

这些编号对应 MD Workflow Stage 1–5。

Stage / Step 目录可以在正式 Skill generation 前预留，因此：

```text
目录存在 ≠ Skill 已生成 ≠ runtime authority 已激活
```

当前建设状态和 current entry 必须读取：

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`

Manager 与 Task Execution runtime 是独立的 unnumbered packages：

```text
00_manager/
00_runtime/
```

科研 Skill 不再按 Workflow / Operation / Validator 分类。Validation 默认跟随结果 owner；只有复杂、独立且可复用时才拆 supporting Skill。

## 3. Non-Skill infrastructure

以下目录不是 Scientific Skill roots，不占用 Stage 编号：

```text
evals/      # tests / fixtures / validation evidence / benchmark
tools/      # current shared deterministic tools
legacy/     # old contracts / runtime / runtime-dependent tools
```

历史设计 Markdown 位于 `00_authoring/archive/`。

`legacy/` 与 `00_authoring/archive/` 不是 current authority，普通 runtime / authoring 不默认读取。

## 4. Skill / freeze / status boundary

Architecture freeze 位于：

`00_authoring/architecture_freezes/`

freeze 可以详细到足以直接支持后续 Skill generation，但：

```text
architecture frozen
≠ Skill generation 已获许可
≠ active SKILL.md
```

任何 authoring 窗口如果改变了 Stage / Step 的真实建设状态，例如：

```text
design → frozen
freeze-only → active Skill generated
active Skill → validation milestone changed
current → superseded / retired
```

都必须同步 `MD_WORKFLOW_MASTER_PLAN.md`；具体规则见 `00_authoring/SKILL.md` 和 `00_authoring/references/multi_window_authoring_protocol.md`。

不得仅凭目录或历史 `SKILL.md` 文件存在推断 runtime authority。

## 5. Tool boundary

Tool 是确定性能力，不是科学决策层或 parser gate。

Current shared Tool root：`tools/`。

只有已经适配 current Lightweight / Skill interface、完成测试并明确 reactivated 的 Tool 才进入 `tools/tool_registry.yaml`。

旧 runtime-dependent Tool 保存在 `legacy/tools/`，不得因为历史 ACTIVE 状态自动用于 current runtime。

## 6. Read/write ownership

Authoring 必须遵守：

```text
read scope 可以宽
write ownership 必须窄
```

当前 Skill 可以消费其他 owner 的正式结果/接口，不能替其定义内部步骤、默认参数、validation、official results 或文件生命周期。

状态同步只有一个窄例外：当前 Skill/freeze authoring 直接造成的 Master Plan 状态/current-entry 变化，按多窗口协议在无显式 writer 冲突时可以由当前窗口同步；这不扩展科学内容 ownership。

提出或实施迭代修改前恢复：

```text
已做过
已否定
仍未验证
```

没有新证据改变前提时，不恢复已否定方案。

## 7. Project records

真实项目默认：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

`task_index.md` 只做任务导航；`tasks/Txxxx.md` 保存动态计划与最小恢复上下文；`project_result_index.md` 只做正式结果检索。

## 8. Safety

- 不修改受保护来源文件，除非有明确授权；
- 未经授权不删除、覆盖或批量移动科研结果；
- 破坏性或不可逆动作必须确认；
- Tool 默认不联网、不嵌入 LLM、只写授权路径；
- 不自动通过单位计费数据库下载内容。

## 9. Current authority

```text
Authoring                  → 00_authoring/SKILL.md
Skill boundaries           → 00_authoring/references/skill_boundaries.md
Cross-Stage runtime        → 00_runtime/SKILL.md
Stage catalog/status       → 00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md
Stage/Step architecture freeze → 00_authoring/architecture_freezes/
Manager                    → 00_manager/SKILL.md
Scientific Skills          → entries explicitly marked current in Master Plan
Current shared Tools       → tools/
Evaluation infrastructure  → evals/
Legacy executable material → legacy/
Historical design material → 00_authoring/archive/
```
