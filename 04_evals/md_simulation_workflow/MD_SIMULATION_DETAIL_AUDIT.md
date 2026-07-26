# MD Simulation Detail Audit

## Status

```yaml
status: CORRECTION_REQUIRED
branch: draft/md-simulation-skills
review_scope: md_simulation contract details
runtime_ready: false
implementation_may_start: false
```

本记录在继续实现前核对对象生成链、schema 可实例化性、续跑/重试语义、artifact 谱系和阶段出口。审计完成前不增加 backend 或 parser 实现。

## 已核对的权威边界

```text
md_preparation_workflow
→ VALIDATED SYSTEM
→ md_simulation_workflow
→ protocol / plan / MDP / TPR / execution
→ VALIDATED MD_OUTPUT
```

该阶段边界保持不变。只有 SYSTEM 的结构、拓扑、盒子、溶剂或离子改变时返回 `md_preparation_workflow`。

## P0：必须先修复

### 1. Execution spec 没有生成者

现状：

- `md_run_execution` 要求不可变 `md_run_execution_spec.yaml`；
- Workflow 从 VALIDATED MD_INPUT 直接进入 execution；
- 当前没有 Operation/Validator 负责生成和验证 execution spec；
- Manager、Workflow 和 execution Operation 均不应临时拼装该业务对象。

结论：执行链不闭合。

修正：增加 execution specification/validation task unit，或明确将 execution spec 作为 input preparation 的正式输出并由专属 Validator 一并核验。优先采用独立 task unit，因为 backend、资源和 restart attempt 可以在 MD_INPUT 生成后再解析。

### 2. 缺少 execution attempt 模型

现状：

- run unit 同时承担科学片段身份和具体执行实例；
- execution spec 包含 `task_id`，但没有稳定 `execution_spec_id` 和 `attempt_id`；
- retry、scheduler resubmission、same-TPR continuation 无法与原 execution 区分；
- `allow_overwrite: false`、`submit_once: true` 与 append continuation 修改既有输出冲突；
- status/output Validators 只按 run unit 对齐，无法唯一选择当前 attempt。

结论：恢复、续跑和重提会发生身份混淆。

修正：

```text
run unit = 科学运行片段
execution attempt = 对该 run unit 的一次具体执行或提交
```

每个 attempt 必须有稳定 ID、独立 execution spec、command/submission/status evidence 和 attempt directory。same-TPR continuation 是新 attempt，不是新的科学 role。

### 3. 阶段出口缺少聚合对象

现状：

- 每个 run unit 生成一个 run-level MD_OUTPUT；
- segmented production 可能包含 `md.1`、`md.2`、`md.3` 多个有效输出；
- completion Validator 要求唯一 `final_md_output_artifact_set_id`；
- 没有 Operation/Validator 生成包含所有必需 segment 的 stage-level output manifest。

结论：只选择最后一个 run output 会丢失早期轨迹；选择多个又违反唯一出口要求。

修正：增加 simulation output assembly/validation，生成唯一 stage-level `MD_OUTPUT` collection manifest，引用范围内 required run-level MD_OUTPUT artifact sets，不复制或拼接轨迹。

## P1：架构一致性问题

### 4. CONTINUATION 不应作为科学 role

当前 role 枚举包含：

```text
ENERGY_MINIMIZATION | EQUILIBRATION | PRODUCTION | CONTINUATION | CUSTOM
```

continuation 描述执行方式，不描述科学角色。production continuation 仍是 PRODUCTION，equilibration continuation 仍是 EQUILIBRATION。

修正：从 role 移除 `CONTINUATION`。restart/continuation 进入 execution attempt spec。

### 5. Protocol 混入环境和运行配置

当前 protocol/plan 包含：

- grompp executable/version；
- backend type；
- resource profile；
- execution mode。

这些字段不全属于科学协议。改变主机、GROMACS 路径或调度后端不应自动产生新的科学 protocol/plan。

修正：

- protocol：科学片段、MDP 来源/生成要求、start-state、完成标准；
- run-input specification：grompp 输入与显式 warning policy；
- execution-attempt specification：backend、资源、restart、append/noappend 和提交策略。

### 6. MDP 的生成链尚未冻结

当前 schema 要求 MDP file identity，input preparation 只复制/使用已有 MDP，不生成参数化 MDP。

因此必须明确二选一：

1. v1 只支持用户提供或已存在的最终 MDP；或
2. 增加 template + typed overrides 的 MDP materialization/validation。

根据既有设计“EM/平衡模板交给 Operation Skill”，应采用方案 2；禁止自由文本替换和隐式默认值。

### 7. Protocol 与 plan 复制同一科学字段

两份 schema 都完整保存 run unit role、依赖、MDP、start-state、grompp、execution policy 和 completion criteria。

风险：

- 同一概念存在两个 owner；
- schema 与字段修改必须双写；
- plan Validator 主要工作变成复制一致性核对。

修正：protocol 是科学配置唯一 owner；plan 保存 protocol identity、run-unit projection、DAG/route projection 必需派生字段、未决 gate 和 revision lineage。不得再次拥有全部科学参数。

### 8. 决策来源缺少稳定 typed parameter interface

共享 `decision_record` 主要保存 selected option 和 user statement。任意温度、步数、耦合参数不能依靠自由语言解释后直接进入 protocol。

修正：protocol specification 只接受：

- 已验证的结构化 protocol input；
- 精确、可确定解析的 decision option；
- 带 hash 的文件或模板；
- route scope 中非科学的范围字段。

无法确定解析的内容必须形成 confirmation item。

### 9. 输出 role 和 metric ID 尚无 registry

`expected_outputs[].role` 为自由字符串，`metric_id` 也没有 ACTIVE registry。不同 Skill 可能对同一文件/指标使用不同名称。

修正：在启用 parser/Validator hard gate 前建立受控 output-role registry 和 metric registry。registry owner 由主窗口裁决。

## P2：schema 与约束细节

- `start_state: SYSTEM` 当前未禁止非空 checkpoint；
- target step/time 可以同时为空，需要明确仅 normal termination 是否足够；
- execution spec 使用 `task_id` 作为对象身份，不利于跨 task 恢复；
- paths 尚未统一规定 project-relative/absolute 与规范化规则；
- plan/protocol 不是共享 artifact type，Manager 如何标记 validated/superseded 尚未冻结；
- JSON Schema 无法单独保证 run-unit ID、field provenance path 等跨数组唯一性，必须由 Validator 实现；
- append continuation 会修改既有文件，与 artifact immutability 和 hash lineage 冲突，v1 应优先限定 NOAPPEND，或建立显式 mutable-output protocol；
- 同一 Workstream 中独立 run units 是否并行仍未冻结。

## 修正顺序

```text
A. 冻结 run unit / execution attempt / output collection 三层对象
B. 修正 role、continuation 和 directory model
C. 闭合 MDP、MD_INPUT、execution spec 的生成链
D. 精简 protocol/plan owner，拆分 runtime configuration
E. 增加 stage-level output assembly
F. 修订 Workflow、Validators、schemas 和 fixtures
G. 执行 schema/static/fixture tests
H. 通过后才设计 backend/parser Tools
```

## 当前结论

```yaml
contract_detail_audit: completed
blocking_findings:
  P0: 3
  P1: 6
  P2: 8
next_action: object_model_correction
```

在 A–F 完成前，不应同步 `stage_registry.yaml` 为 connected，也不应开始真实 GROMACS/backend 实现。