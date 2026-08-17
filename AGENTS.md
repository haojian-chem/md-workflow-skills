# MD Workflow Project Instructions

## 1. Repository modes

本仓库同时用于真实 MD 项目运行和 Skill / Tool authoring。Skill repository 与真实 MD project root 必须区分。

真实 MD 项目默认使用 Lightweight Runtime v2：

```text
Manager
→ Task Sheet
→ long-lived Task Execution Agent
→ current main Skill
→ 按需 references / supporting Skills / deterministic Tools
```

Manager 请求读取 `00_manager/SKILL.md`；任务执行从目标 `Txxxx.md` 和当前 Step Skill 开始。普通执行不返回 Manager 调度。

Skill authoring / maintenance 默认启动链：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

之后只按当前任务需要读取 architecture freeze、相邻 Skill、project design、Tool guide 或 coordination records。

## 2. Current scientific Skill roots

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

这些编号对应 MD Workflow Stage 1–5。

Manager 是独立 package：`00_manager/`。

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

## 4. Stage 3

Stage 3 — System construction / solvation 已冻结为：

```text
3.1 Periodic box construction
3.2 Solvent addition
3.3 Ion addition
```

Current source entry：`03_md_preparation/SKILL.md`。

Architecture authority：`00_authoring/architecture_freezes/WORKFLOW3_STAGE3_ARCHITECTURE_FREEZE.md`。

3.3 专用 minimal `genion.mdp` 的精确模板内容和 representative execution validation 尚未完成；不得用 Stage 4 MDP 伪代替。

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
Cross-Stage runtime        → 00_authoring/project_design/lightweight_runtime_v2_spec.md
Stage catalog/status       → 00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md
Stage architecture freeze  → 00_authoring/architecture_freezes/
Manager                    → 00_manager/SKILL.md
Scientific Skills          → current Stage root / Step SKILL.md
Current shared Tools       → tools/
Evaluation infrastructure  → evals/
Legacy executable material → legacy/
Historical design material → 00_authoring/archive/
```
