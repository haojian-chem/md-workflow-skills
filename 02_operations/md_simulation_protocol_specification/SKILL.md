---
name: md_simulation_protocol_specification
description: 将 VALIDATED SYSTEM、已解决决定、明确 MDP 或模板及阶段范围物化为 simulation_protocol_spec candidate。该 Operation 只结构化已明确内容，不补充默认模拟流程或科学参数。
---

# 目标

生成 `md_simulation_plan_materialization` 的结构化输入：

```text
VALIDATED SYSTEM
+ resolved decision records
+ explicit MDP/template files
+ resolved route scope
→ simulation_protocol_spec.yaml candidate
→ md_simulation_protocol_validator
```

# 职责边界

负责：

- 读取 SYSTEM artifact、resolved decisions、route scope 和明确文件；
- 物化 run unit、依赖、role、start state、grompp、execution policy、expected outputs 和 completion criteria；
- 为生成字段记录 decision/file provenance；
- 将未决项分为 `PLAN_VALIDATION | INPUT_PREPARATION | EXECUTION`；
- 对无法唯一解释的内容返回 confirmation items；
- 写 protocol spec candidate 和 report；
- 返回 Operation result，交给专属 Validator。

不负责：

- 自动添加 EM、NVT、NPT 或 production；
- 自动选择温度、压力、步数、时间步长、约束、coupling、random seed、maxwarn 或 acceptance threshold；
- 自动选择 MDP、template、checkpoint 或上游输出；
- 修改 SYSTEM、MDP 或 topology；
- 生成 plan、TPR 或运行模拟；
- 修改 decision/state/record；
- 直接向用户提问或自行宣布通过。

# 输入

使用组合 task：

```text
operation: md_simulation_protocol_specification
validator: md_simulation_protocol_validator
mode: OPERATION_WITH_VALIDATOR
```

任务必须提供：

- Focus Workstream 和 resolved route scope；
- VALIDATED SYSTEM artifact records；
- 所有影响本协议的当前 RESOLVED decision records；
- 用户或项目明确提供的 MDP/template file records；
- 旧 protocol spec，如为 revision；
- allowed read/write、forbidden paths 和 detail paths。

输出必须符合：

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_protocol_spec.schema.yaml
```

# Preflight

确认：

- task、Workstream 和 scope 一致；
- SYSTEM 为 VALIDATED；
- decision records 为当前有效 RESOLVED 状态；
- superseded/withdrawn decisions 不作为来源；
- MDP/template 可读且 hash 一致；
- 输出位于 `04_md_simulation/00_plan/`；
- 新 spec 不覆盖旧版本；
- 管理目录不可写。

# 物化规则

spec 中每个科学字段必须由以下来源明确支持：

- resolved decision 的 selected option；
- resolved decision 的用户原话中明确且唯一的值；
- 用户提供的 MDP/template 内容；
- SYSTEM 或上游 validated artifact identity；
- resolved route scope。

不得把模型经验、文件名或常见实践作为来源。

只有明确声明的 run unit 才能写入。每个 run unit 必须明确：

- ID、role、sequence 和 depends_on；
- work directory；
- MDP identity；
- SYSTEM 或 prior-run start state；
- grompp 设置；
- expected outputs；
- completion criteria。

backend/resource 可以显式保持 UNRESOLVED，并在 execution barrier 处理。

以下情况不得猜测：

- “跑标准流程”或“按默认参数”；
- 多个 MDP/template/checkpoint 候选未选择；
- run unit 顺序或依赖不明确；
- duration、step、threshold 或 scientific setting 无法唯一映射。

Operation 先完成可安全部分，再汇总 unresolved items 和 confirmation items。存在 PLAN_VALIDATION 未决项时，candidate 不得进入 plan materialization gate。

protocol 变化时生成新 version 并记录 `supersedes_spec_id`，不覆盖旧 spec。

# 默认输出

```text
04_md_simulation/00_plan/
├── simulation_protocol_spec.yaml
├── md_simulation_protocol_specification_report.yaml
└── protocol_specification.log
```

# 执行流程

1. 解析 task、scope、SYSTEM、decisions 和 files；
2. 过滤当前有效 decisions；
3. 提取明确 run units 和字段；
4. 建立 field provenance；
5. 汇总和分类未决项；
6. 在临时路径生成 spec/report；
7. schema-validate candidate；
8. 核验 source identities；
9. 原子提交；
10. 返回 Operation result并进入专属 Validator。

# Outcome codes

- `SIMULATION_PROTOCOL_SPECIFIED`；
- `SIMULATION_PROTOCOL_SPECIFIED_WITH_DEFERRED_ITEMS`；
- `SIMULATION_PROTOCOL_DECISIONS_INCOMPLETE`；
- `SIMULATION_PROTOCOL_SOURCE_AMBIGUOUS`；
- `SIMULATION_PROTOCOL_MDP_IDENTITY_INVALID`；
- `SIMULATION_PROTOCOL_SYSTEM_INVALID`；
- `SIMULATION_PROTOCOL_OUTPUT_CONFLICT`；
- `SIMULATION_PROTOCOL_SPECIFICATION_INTERNAL_FAILURE`。

# 返回与自检

成功时只创建 protocol spec candidate 和 report，不创建 plan 或 artifact candidate。

- [ ] 每个科学字段有明确来源；
- [ ] 未添加默认 run units 或参数；
- [ ] superseded decisions 未被使用；
- [ ] files 和 hashes 可追溯；
- [ ] 歧义已返回 confirmation items；
- [ ] 旧 spec 未覆盖；
- [ ] 未生成 plan/TPR 或执行模拟；
- [ ] 未写管理目录；
- [ ] 未自行宣布通过。