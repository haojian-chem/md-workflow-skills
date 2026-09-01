# Workflow 1 / Stage 1.9 Structure preparation validation architecture record

Status: **IMPLEMENTED ARCHITECTURE RECORD — CURRENT RUNTIME OWNER: `01_structure_preparation/1.9_validation/SKILL.md`**

## 0. 文档定位

本文件保存 `1.9 Structure preparation validation` 在正式 Skill 生成前已经冻结的架构定位。

当前 active runtime / scientific authority 为：

```text
01_structure_preparation/1.9_validation/SKILL.md
```

正式 Skill 已生成后，具体检查项目、reference 使用方式、报告格式、reuse、结果生命周期和 completion 语义由 current `SKILL.md` 拥有；本文件不再维护第二套平行的可变执行规范，也不得作为 runtime Skill 使用。

历史 pre-generation 细节可通过 Git history 审计。此前迁移来源包括：

- former active pseudo-Skill: `01_structure_preparation/1.9_validation/SKILL.md`, blob `8219921970d07dea923699f7dc74f4e5fa589c83`
- historical final validation source: `02_validators/structure_preparation_validator/SKILL.md`, blob `ae0dfe2a240e7b89fe446520156c62bfa6b2cc51`

## 1. Frozen architecture

1.9 是 Stage 1 的最终只读检查步骤。

架构边界固定为：

- 直接检查 1.8 形成的 Stage 1 final structure / map；
- 对最终结构执行 Stage 1 结束前所需的独立结构检查和目标力场 / CCD 对照检查；
- 使用 1.2 已物化的 classification / relation information，不在 1.9 重新分类或重新判断 relation；
- 不在 1.9 修改、repair 或静默纠正 PDB、map 或上游正式结果；
- 多个 target 独立检查、独立形成 1.9 报告；
- 1.9 本身就是当前 Stage 1 final validation Step，不恢复历史独立 Validator role hierarchy。

## 2. Stage boundary

1.9 只处理 Stage 1 final heavy-atom structure 在进入 Stage 2 前的最终检查。

Stage 2 的全原子拓扑生成、标准残基加氢、非标准残基参数化和后续 topology assembly 不属于 1.9。

Stage 1 与 Stage 2 的实际 handoff 和当前任务是否继续推进，以 current Stage 1 main Skill、current 1.9 Skill 以及 Task Execution 规则为准。

## 3. Current implementation

Active Skill：

```text
01_structure_preparation/1.9_validation/SKILL.md
```

Stage main entry：

```text
01_structure_preparation/SKILL.md
```

Project-level implementation status owner：

```text
00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md
```
