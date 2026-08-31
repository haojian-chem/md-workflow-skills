# Workflow 3 / Stage 3 architecture freeze

## 0. 文档定位

本文件记录 MD Workflow Stage 3 — System construction / solvation 的当前架构、
职责边界、内部 operation 习惯、Task Sheet 维护方式和正式结果接口。

Status: **FROZEN — NO ACTIVE SKILL GENERATION APPROVED YET**

未来 Stage-level runtime entry 固定为：

`03_md_preparation/SKILL.md`

Stage 3 不设置编号化 sub-stage。周期盒构建、溶剂添加和离子添加是 Stage 3 main Skill
内部按任务规划和执行的 operation types，不建立独立 `SKILL.md`。

原 `3.1 / 3.2 / 3.3` step-level freezes 已由本文件取代并移入 authoring archive。
Architecture freeze 完成不等于已经批准生成 active Skill。

## 1. Stage 3 职责

Stage 3 main Skill 读取当前 Task Sheet 中的体系构建目标、处理对象和已经明确的约束，
以当前拓扑整合正式结果为主要上游依据，完成：

```text
理解当前体系构建目标
→ 读取当前结构与拓扑/参数文件集合
→ 形成并维护当前 Stage 3 operation plan
→ 执行实际体系构建 operations
→ 完成各 operation 的必要检查
→ 生成 system_construction_result.yaml
```

Stage 3 当前定义三类内部 operation：

```text
periodic_box_construction
solvent_addition
ion_addition
```

普通水溶液体系的常见顺序为：

```text
periodic_box_construction
→ solvent_addition
→ ion_addition
```

实际 operation plan 由当前结构—拓扑状态和 Task Sheet 中的体系构建目标决定；
operation 可以省略、重复或按当前任务需要调整顺序。

## 2. 输入、检查证据与 reuse

Stage 3 以当前 Task Sheet 指定的：

`topology_integration_result.yaml`

作为主要上游正式结果，并从其中记录的实际完整路径定位当前结构文件、体系主 `.top`
以及当前拓扑/参数文件集合所需的 `.itp` 和外部拓扑定义。
不根据默认 basename、目录顺序或文件修改时间重新推断这些文件。

若存在与当前拓扑整合对象对应的：

`topology_validation_result.yaml`

Stage 3 读取其中记录的检查事实，分析已记录问题对当前体系构建的影响；
发现可能影响后续构建或模拟准备的风险时，在用户可见回复和当前 Task Sheet 中说明。
当前结构与拓扑/参数文件集合仍由拓扑整合正式结果定位。

Stage 3 遵守仓库级 Task Execution reuse 规则。已有 `system_construction_result.yaml`
在其上游结构—拓扑对象与当前周期盒、溶剂、离子和其它结果相关要求均明确等价，
且最终结构文件和体系主 `.top` 仍可定位时，可以直接复用。

## 3. Operation plan 与工作目录

Stage 3 main Skill 在当前 Task Sheet 的 Stage 3 条目内部补充并维护 operation plan，
使执行 Agent 能恢复当前 operation 顺序、type、状态、工作目录、当前结构文件、
当前体系主 `.top`、已完成 operation 的关键结果和 Stage 3 正式结果入口。

实际结果改变后续构建需要时，Stage 3 更新尚未完成的 operation plan；
已经实际执行并形成有意义历史的 operation 继续保留在 Task Sheet 中。

需要本地执行时，Stage 3 使用：

`<project_root>/03_md_preparation/<task_id>/`

每次实际 operation 建立独立目录，使用两位数字表示当前 Task 内的实际执行顺序：

```text
03_md_preparation/<task_id>/
├── 01_periodic_box_construction/
├── 02_solvent_addition/
├── 03_ion_addition/
└── system_construction_result.yaml
```

重复或重排 operation 时继续使用下一个顺序号，例如：

```text
01_periodic_box_construction/
02_solvent_addition/
03_periodic_box_construction/
04_solvent_addition/
05_ion_addition/
```

`01_ / 02_ / ...` 只表示当前 Task 内的 operation 顺序，不是 MD Workflow Step identity。

`.gro`、`.top`、`.itp`、`.mdp` 和 `.tpr` 等实际文件只设置默认 basename 或命名倾向；
正式结果记录保存实际完整路径。

Stage 3 不原地覆盖上游正式结构文件、体系主 `.top` 或 `.itp`。
需要由 `gmx solvate -p` 或 `gmx genion -p` 修改体系组成时，
先在当前 operation 目录形成可修改的派生体系主 `.top`。

## 4. Internal operation habits

### 4.1 Periodic box construction

当前使用：

`gmx editconf`

参数习惯：

```text
-f     当前结构文件
-o     当前 operation 的输出结构文件
-c     显式保留，表达构盒 / 调整后的居中意图
-box   当前任务给出明确 box dimensions 时使用
-d     当前任务给出 solute-to-boundary distance 时使用
-bt    按当前任务要求确定 box type
```

`-box` 与 `-d` 按当前任务要求选择。
GROMACS 中二者本身会隐含居中；Stage 3 仍保留 `-c` 作为显式命令习惯。

完成当前 operation 前检查：

1. `gmx editconf` 进程正常结束；
2. 溶质位于生成周期盒的中心。

该 operation 通常只生成新的结构文件；体系主 `.top` 未改变时，
不把它记录为当前 operation 新生成的结果。

### 4.2 Solvent addition

当前使用：

`gmx solvate`

参数习惯：

```text
-cp    当前结构文件
-cs    当前任务采用的 solvent coordinate / template
-p     当前 operation 中可修改的体系主 .top
-o     当前 operation 的输出结构文件
```

普通情况下沿用 GROMACS 2022 的默认：

```text
-scale  0.57
-radius 0.105 nm
```

命令可以依赖软件默认值；若当前任务采用其它值，在 Task Sheet 当前 operation 中记录实际设置。

完成当前 operation 前检查：

1. `gmx solvate` 进程正常结束；
2. 当前体系主 `.top` 中的溶剂分子记录与数量已由本次操作正常更新。

### 4.3 Ion addition

当前内部执行结构为：

```text
dedicated genion.mdp
→ gmx grompp
→ current-operation .tpr
→ gmx genion
→ ionized structure + updated system .top
```

Stage 3 Skill package 需要携带一个只用于生成 `gmx genion` 输入 `.tpr` 的 minimal `genion.mdp`。
它不承担 energy minimization、equilibration 或 production simulation 的参数语义。
精确模板内容与代表性执行验证在正式 Skill generation 时完成。

`gmx grompp` 参数习惯：

```text
-f    dedicated genion.mdp
-c    当前结构文件
-p    当前 operation 中可修改的体系主 .top
-o    当前 operation 的 .tpr
```

`gmx genion` 参数习惯：

```text
-neutral        当前任务要求 neutralization 时使用
-conc 0.154     生物体系在用户和 Task Sheet 未指定其它盐浓度或离子组成时使用
-pname/-nname   按当前实际离子拓扑定义确定
replacement     选择当前实际需要被替换的主体溶剂 group
```

用户或 Task Sheet 明确给出的盐浓度或离子组成覆盖生物体系的 `0.154 M` 默认倾向。

完成当前 operation 前检查：

1. `gmx grompp` 进程正常结束并生成当前 operation 的 `.tpr`；
2. `gmx genion` 进程正常结束；
3. 当前体系主 `.top` 中被替换的 solvent 和新增 ion 记录已由本次操作正常更新。

`.mdp` 和 `.tpr` 保留在 operation 目录中作为执行文件，不进入项目结果索引。

## 5. 正式结果

Stage 3 固定生成：

`system_construction_result.yaml`

正式 Skill generation 时，详细结果接口下放到：

`03_md_preparation/references/results.md`

结果结构冻结为：

```yaml
references:
  INTEGRATION: /absolute/path/to/topology_integration_result.yaml
  VALIDATION: /absolute/path/to/topology_validation_result.yaml

results:
  operations:
    - directory: /absolute/path/to/01_periodic_box_construction
      type: periodic_box_construction
      structure: /absolute/path/to/actual_boxed_structure.gro

    - directory: /absolute/path/to/02_solvent_addition
      type: solvent_addition
      structure: /absolute/path/to/actual_solvated_structure.gro
      top: /absolute/path/to/actual_solvated_system.top

    - directory: /absolute/path/to/03_ion_addition
      type: ion_addition
      structure: /absolute/path/to/actual_ionized_structure.gro
      top: /absolute/path/to/actual_ionized_system.top

  final:
    structure: /absolute/path/to/actual_final_structure.gro
    top: /absolute/path/to/actual_final_system.top
```

结果规则：

- `references` 遵守仓库级结果生成规则；
- `INTEGRATION` 记录本次实际采用的拓扑整合正式结果；
- `VALIDATION` 只在本次实际读取并分析对应拓扑终检结果时记录；
- `results.operations` 按实际执行顺序记录；
- 每项 operation 只记录目录、type 及该 operation 实际保留的结构文件和 / 或体系主 `.top`；
- 没有由当前 operation 生成的结果字段不建立占位；
- `results.final` 只记录最终结构文件和最终体系主 `.top`；
- Stage 3 不生成或登记 atom map；
- 所有路径使用实际完整绝对路径；
- `.gro` 和 `.top` basename 不是固定接口。

项目结果索引只登记：

`system_construction_result.yaml`

各 operation 产生的 `.gro` / `.top`、最终 `.gro` / `.top`、`.mdp`、`.tpr`
和 operation directory 均通过该 YAML 定位，不分别登记到项目结果索引。

## 6. 完成条件与 implementation status

Stage 3 工作项完成需要：

1. 当前 operation plan 中实际需要的 operations 已完成；
2. 每个已执行 operation 已完成本文件规定的检查；
3. `system_construction_result.yaml` 已生成，并能够定位全部保留的 operation 结果以及最终结构文件和体系主 `.top`；
4. 当前 Task Sheet 的 Stage 3 条目已更新；
5. `system_construction_result.yaml` 已登记到项目结果索引。

Current architecture 已冻结；active Skill generation 尚未获批。

正式生成时仍需：

- 生成 `03_md_preparation/SKILL.md`；
- 生成 `03_md_preparation/references/results.md`；
- 建立并验证 dedicated minimal `genion.mdp`；
- 完成代表性或确定性执行验证。
