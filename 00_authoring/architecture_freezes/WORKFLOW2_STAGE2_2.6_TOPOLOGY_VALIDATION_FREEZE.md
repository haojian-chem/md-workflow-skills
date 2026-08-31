# Workflow 2 Stage 2.6 Topology validation architecture record

Status: IMPLEMENTED ARCHITECTURE RECORD

## 0. 文档定位

本文件记录 `2.6 Topology validation` 在 active Skill 生成时已经确认的架构和职责边界。

Current runtime authority 为：

```text
02_topology_preparation/2.6_topology_validation/SKILL.md
02_topology_preparation/2.6_topology_validation/references/results.md
02_topology_preparation/2.6_topology_validation/references/grompp_validation.mdp
```

后续执行规则、结果字段和预设参数的修改由上述 active Skill package 拥有；本文件不再维护一套平行的可变规范。

旧 Stage 2 综合冻结文件：

`WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

中与 topology validation 的具体依赖、检查内容、结果记录和 GROMACS 预处理有关的旧文本已经被本记录及 active
Skill package 取代，不得作为 current execution source 恢复。

## 1. 已实现职责

Topology validation 对当前拓扑整合正式结果进行独立、只读终检。

当前职责检查已经形成的结构文件和拓扑文件，不修改结构文件、体系 `.top`、`.itp`、map 或参数文件，也不在发现
问题时顺手修正拓扑。

## 2. 已实现输入边界

直接正式依赖固定为：

1. `classification_result.yaml`；
2. `topology_integration_result.yaml`。

结构文件、map、体系 `.top` 和 `.itp` 均从拓扑整合正式结果读取实际路径；不根据默认 basename、目录顺序或
“最新文件”重新推断。

## 3. 已实现 reuse 规则

Topology validation 不设置 reuse。

每次实际进入当前工作项，都针对当前两个直接正式依赖及其记录的当前结构文件和拓扑文件重新执行规定检查，不使用
既有 `topology_validation_result.yaml` 跳过本次检查。

## 4. 已实现检查范围

Active Skill 固定执行六项检查：

1. 检查体系 `.top` 中各 `#include` 指向的文件是否存在、是否可读取；
2. 按体系 `.top [ molecules ]` 和对应 `moleculetype [ atoms ]` 展开拓扑，逐项核对当前结构文件中的分子、
   residue 和 atom；
3. 检查 `classification_result.yaml` 中 `judgment = CONFIRMED` 且
   `topology_effect_applied = true` 的 topology-linked 关系是否按实际采用的 topology-linked 参数化结果写入
   最终拓扑；
4. 检查 topology-linked 参数化正式结果中 `standard_atom_deletions` 指定的标准残基原子是否已经从当前结构文件
   和最终 `moleculetype [ atoms ]` 中删除；
5. 逐 atom 检查 `charge_modification_scope` 中标准残基一侧的指定电荷是否写入最终
   `moleculetype [ atoms ]`，正式结果只按 residue 记录检查 atom 数量和电荷差异数量；
6. 使用 `gmx grompp` 检查当前结构文件和体系 `.top`，记录实际 GROMACS version、命令、return code、note、
   warning 和 error。

`COVALENT_CONNECTION` 与 `METAL_COORDINATION` 都以当前 topology-linked 参数化结果和拓扑整合结果实际采用的
拓扑项为检查依据；Topology validation 不根据 `relation_type` 另行发明拓扑表示规则。

## 5. 已实现 GROMACS 预处理边界

Active Skill package 提供：

`references/grompp_validation.mdp`

作为默认检查参数。该预设关闭周期性边界条件和非键截断，仅用于 `gmx grompp` 预处理，不定义后续模拟方案；
生成的临时 `.tpr` 不作为模拟输入。

Agent 可以在实际检查需要时生成等价的任务级 `.mdp`，但必须在正式结果中记录实际执行命令，且不得使用
`-maxwarn` 强制越过 warning。

## 6. 已实现正式结果

唯一正式结果为：

`topology_validation_result.yaml`

该 YAML 使用既定 `references` 和六个 `check_results` 字段，只记录实际检查对象和检查结果，不记录 `PASS`、
`FAIL`、`COMPLETE`、整体结论或阻断性结论。

项目结果索引只登记 `topology_validation_result.yaml`；当前结构文件、map、体系 `.top`、`.itp`、检查用 `.mdp`
和临时 `.tpr` 不作为当前职责的新结果重复登记。

完成六项检查并生成 `topology_validation_result.yaml` 后，当前工作项完成。检查中发现的问题继续保留在正式结果中，
不改变当前工作项已经完成检查并生成正式结果这一事实。

## 7. 已退出的旧规则

Current topology validation 不执行或记录：

- map 与结构文件的独立逐原子终检；
- map provenance 的独立终检；
- 当前体系总电荷判据；
- 在 `gmx grompp` 之外另建 atom type / 参数定义查找检查；
- `package completeness`、`internal consistency`、`charge/connectivity sanity` 等未展开的抽象检查标签；
- 六项检查的 PASS / FAIL、overall conclusion 或 blocking finding；
- 标准残基一侧电荷修改的逐 atom 电荷明细；
- 脱离实际 topology-linked 参数化结果的 `METAL_COORDINATION` 拓扑表示判据。
