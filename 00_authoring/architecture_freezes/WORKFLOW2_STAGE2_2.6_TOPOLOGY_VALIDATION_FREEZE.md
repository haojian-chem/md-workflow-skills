# Workflow 2 Stage 2.6 Topology validation architecture record

Status: IMPLEMENTED ARCHITECTURE RECORD

## 0. 文档定位

本文件记录 `2.6 Topology validation` 在 active Skill 生成及后续检查中已经确认的架构与职责边界。

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

## 1. 已实现职责与对象范围

Topology validation 对当前 Task Sheet 工作项指定的处理对象执行独立、只读终检。

Task Sheet 是当前工作项处理对象的确定依据。`topology_integration_result.yaml` 用于定位当前工作项实际检查的结构文件、
map、体系 `.top`、`.itp` 和 `moleculetypes`，不替代 Task Sheet 建立新的处理对象。

读取 `classification_result.yaml` 时，只消费能够映射到当前处理对象的 residue 身份、`topology_class` 和
`topology_linked_checks`；不要求同一 model 中未进入当前处理对象的其它内容出现在当前拓扑中。

当前职责不修改结构文件、体系 `.top`、`.itp`、map 或参数文件，也不在发现问题时顺手修正拓扑。

## 2. 已实现输入边界

直接正式依赖固定为：

1. `classification_result.yaml`；
2. `topology_integration_result.yaml`。

结构文件、map、体系 `.top` 和 `.itp` 均从拓扑整合正式结果读取实际路径；不根据默认 basename、目录顺序或
“最新文件”重新推断。

正式结果不另建 `target_id` 或平行对象记录。当前检查使用的两个直接正式依赖和具体检查文件均由结果内部
`references` 的完整绝对路径记录。

## 3. 已实现 reuse 规则

Topology validation 不设置 reuse。

每次实际进入当前工作项，都针对 Task Sheet 当前工作项指定的处理对象、当前两个直接正式依赖及其记录的结构文件和
拓扑文件重新执行规定检查，不使用既有 `topology_validation_result.yaml` 跳过本次检查。

## 4. 已实现检查范围

Active Skill 当前执行六项检查：

1. 检查体系 `.top` 中各 `#include` 指向的文件是否存在、是否可读取；
2. 按体系 `.top [ molecules ]` 和对应 `moleculetype [ atoms ]` 展开拓扑，逐项核对当前结构文件中的分子、
   residue 和 atom；同一检查项内核对条件引用的 position restraint `.itp` 是否覆盖对应 `moleculetype` 的全部
   重原子，且没有对氢原子施加 position restraint；
3. 从依赖文件 `classification_result.yaml` 的 `topology_linked_checks` 读取当前处理对象中
   `judgment = CONFIRMED` 且 `topology_effect_applied = true` 的关系，并检查最终对应 `moleculetype` `.itp` 的
   `[ bonds ]` 是否直接连接关系两端 atom；
4. 检查 topology-linked 参数化正式结果中 `standard_atom_deletions` 指定的标准残基原子是否已经从当前结构文件
   和最终 `moleculetype [ atoms ]` 中删除；
5. 逐 atom 检查 `charge_modification_scope` 中标准残基一侧的指定电荷是否写入最终
   `moleculetype [ atoms ]`，正式结果只按 residue 记录检查 atom 数量和电荷差异数量；
6. 使用 `gmx grompp` 检查当前结构文件和体系 `.top`，记录实际 GROMACS version、命令、进程返回码，并对每项
   note、warning 和 error 记录原始信息及分析。

Topology-linked 检查只区分：

```text
依赖文件 → classification_result.yaml
检查对象文件 → 最终对应 moleculetype 的 .itp
```

不建立额外的“检查来源”概念，也不通过 topology-linked 参数化工作目录反推应检查哪些关系。

## 5. 已实现 GROMACS 预处理边界

Active Skill package 提供：

`references/grompp_validation.mdp`

作为可直接使用的检查起点。执行 Agent 可以根据当前 GROMACS 版本、结构文件和体系 `.top` 判断是否直接使用，
或生成适用于当前预处理检查的任务级 `.mdp`；实际命令必须记录在正式结果中，且检查参数不得解释为后续模拟方案。

默认不启用 `POSRES`、`POSRES_WATER` 或其它条件宏；position restraint `.itp` 已在 `.itp` 检查中核对。不得使用
`-maxwarn` 强制越过 warning。

检查每项 note、warning 和 error 时，需要说明触发原因、其是否反映当前结构或拓扑问题，以及作出该判断的依据。
生成的临时 `.tpr` 不作为模拟输入。

## 6. 已实现正式结果

唯一正式结果为：

`topology_validation_result.yaml`

该 YAML 使用既定 `references` 和六个 `check_results` 字段，只记录实际检查对象和检查结果，不记录 `PASS`、
`FAIL`、`COMPLETE`、整体结论或阻断性结论。

Position restraint 检查结果记录在 `check_results.structure_topology.position_restraints`，不建立第七个顶层检查字段。

项目结果索引只登记 `topology_validation_result.yaml`；当前结构文件、map、体系 `.top`、`.itp`、检查用 `.mdp`
和临时 `.tpr` 不作为当前职责的新结果重复登记。

完成全部规定检查并生成 `topology_validation_result.yaml` 后，当前工作项完成。检查中发现的问题继续保留在正式结果中，
不改变当前工作项已经完成检查并生成正式结果这一事实。

## 7. 已退出的旧规则

Current topology validation 不执行或记录：

- map 与结构文件的独立逐原子终检；
- map provenance 的独立终检；
- 当前体系总电荷判据；
- 在 `gmx grompp` 之外另建 atom type / 参数定义查找检查；
- `package completeness`、`internal consistency`、`charge/connectivity sanity` 等未展开的抽象检查标签；
- 检查项的 PASS / FAIL、overall conclusion 或 blocking finding；
- 标准残基一侧电荷修改的逐 atom 电荷明细；
- 为 position restraint `.itp` 建立独立顶层检查项；
- 通过启用 position restraint 条件宏替代 `.itp` 中的重原子 restraint 检查；
- 在正式结果中另建 `target_id` 或平行对象追溯字段。
