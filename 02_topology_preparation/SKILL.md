---
name: topology-preparation
description: Stage 2 Topology / parameterization 的总 Skill。定义 2.1–2.6 的阶段级关系、当前子环节入口和 Stage 1→2→3 handoff；具体参数化与拓扑处理规则由各 2.x main Skill 拥有。
---

# 2 Topology / parameterization

## Purpose

将 Stage 1 已验证的结构结果推进为完整、可验证、可交给 Stage 3 体系构建的全原子 topology package。

本 Skill 只拥有 Stage 2 的阶段级关系，不复制各 2.x 子环节的内部参数化方法、软件参数、validation 或 official results。

Stage 2 已冻结架构见：

`00_authoring/architecture_freezes/WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

## Catalog

```text
2.1 Parameterization environment and assignment
2.2 Standard residue topology generation
2.3 Topology-linked nonstandard parameterization
2.4 Independent nonstandard parameterization
2.5 Topology integration and assembly
2.6 Topology validation
```

当前已经迁移到本 Stage 目录的详细子环节 Skill：

```text
2.5_topology_integration_and_assembly/SKILL.md
```

其余 2.x 子环节在对应 current Skill 实现完成后放入本 Stage 目录；本文件不为尚未实现的子环节编造替代执行规则。

## Runtime use

Task Execution Agent 从 Task Sheet 确定当前 2.x 子环节后，直接读取该子环节的 current main Skill。

正常执行不需要额外 Workflow / Operation / Validator dispatcher，也不因 Stage main Skill 的存在而强制经过固定 parser 或 Tool。

## Stage-level handoff

- 2.1 建立当前体系的 parameterization environment / assignment，供后续 2.x 使用。
- 2.2 处理标准残基拓扑并建立标准部分 all-atom 基础。
- 2.3 处理 topology-linked nonstandard unit。
- 2.4 处理 independent nonstandard component/type。
- 2.5 只消费上游正式结果并完成 final topology integration / assembly，不重新做上游参数化。
- 2.6 对 2.5 final topology package 做最终 Stage 2 validation；不在验证步骤内静默修复上游问题。

这些说明只定义 handoff；具体内部规则由对应 2.x Skill / current freeze owner 持有。

## Stage boundary

Stage 1 提供最终重原子结构和 identity/mapping；Stage 2 可以生成标准残基 H 和 force-field-specific all-atom topology/order。

Stage 2 完成后应交付经过 2.6 验证的 topology / coordinate / mapping package，供 Stage 3 system construction / solvation 使用。

## Dynamic task plan

2.1–2.6 是 Stage catalog 和默认科学顺序。实际 Task Sheet 可以根据当前体系、已有正式结果和用户要求动态调整尚未执行的后续项，但 applicability / reuse 判断由当前子环节 Skill 在执行期负责，不由本 Stage main Skill复制一套规则。
