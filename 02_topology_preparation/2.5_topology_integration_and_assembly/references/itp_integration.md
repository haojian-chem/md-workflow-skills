# `.itp` 整合

本 reference 在体系整合 `.gro` 与 `integrated.map` 的 residue / atom 顺序已经冻结后读取。

对当前整合需要生成 `.itp` 的每个 `moleculetype`，主拓扑文件命名为：

`<moleculetype name>.itp`

无需独立参数化、直接采用既定拓扑定义的 solvent / ion 不复制为新的主 `.itp`；体系 `.top` 直接引用其实际采用的拓扑定义文件。

## `[ moleculetype ]`

`[ moleculetype ]` 使用已经确定的 `moleculetype` 名称。

`nrexcl` 不是由用户任意指定的独立参数。对本次新生成的 `moleculetype`，根据当前实际采用的来源拓扑和基础力场对 bonded-neighbor exclusion 的定义确定：

- 当前 `moleculetype` 直接继承一个来源 `moleculetype`，且本次整合没有改变其 exclusion 语义时，沿用该来源的 `nrexcl`；
- 当前 `moleculetype` 由多个来源拓扑整合形成时，检查这些来源的 `nrexcl` 及其所属力场 / 参数体系的 exclusion 约定；来源语义一致时采用该共同值；
- 来源值或 exclusion 约定存在冲突时，不按来源顺序、数量多数或固定默认值选择。先根据当前体系实际采用的基础力场、来源拓扑和本次新建立的拓扑连接判断哪套 exclusion 语义适用于当前 `moleculetype`；仍不能唯一确定时，向用户说明冲突来源和科学影响，确认采用的力场 / 拓扑约定后再确定 `nrexcl`，而不是要求用户脱离这些依据直接填写一个数值。

最终实际写入每个本次生成 `moleculetype` 的 `nrexcl` 必须能够追溯到上述来源拓扑 / 力场依据。

## `[ atoms ]`

生成每个 `moleculetype` 的 `.itp` 时，首先整合 `[ atoms ]`。

`[ atoms ]` 中 residue / atom 的顺序必须与已经冻结的体系整合 `.gro` 中该 `moleculetype` 对应部分一致。

标准残基的原子属性以对应标准残基来源 `.itp` 为基础，并应用相关 topology-linked 参数化正式结果中的
`standard_atom_deletions`。topology-linked 非标准残基和独立非标准残基的原子属性从对应
`parameterized_topology.itp` 迁移到当前真实原子。

对 topology-linked 参数化正式结果中 `charge_modification_scope` 列出的真实 residue，使用对应
`parameterization.chg` 中的电荷更新当前生成 `.itp` 的 `[ atoms ]` 中相应 atom 的 `charge`；原子对应通过
`parameterization_model.map` 确定。仅更新该正式范围内实际进入当前 `moleculetype` 的原子。

每个 `moleculetype` 内按当前 residue 顺序从 1 开始连续重新编号 `resnr`；同一 residue 的全部 atom 使用同一
`resnr`。随后按当前 atom 顺序从 1 开始连续重新编号 `[ atoms ] nr`，并令 `cgnr` 与重新编号后的 `nr` 一致。

这里的 `resnr` 和 `nr` 都是当前 `moleculetype` 内的局部编号，不使用体系整合 `.gro` 的全局 residue number
或 atom number 代替。

生成过程中，为当前 `.itp` 中每个 `[ atoms ] nr` 建立能够确定的全部来源 `.itp` 与来源原始 `nr` 对应，
用于后续各拓扑项的编号迁移和来源追踪。一个当前 `nr` 可以对应多个来源 `.itp` 中的原始 `nr`。

## `[ bonds ]` / `[ angles ]` / `[ dihedrals ]`

完成 `[ atoms ]` 后，整合 `[ bonds ]`、`[ angles ]` 和 `[ dihedrals ]`，并按当前 `[ atoms ] nr` 更新所有原子编号。

### 标准残基

保留标准残基来源 `.itp` 中属于当前 `moleculetype` 且仍然有效的 `[ bonds ]`、`[ angles ]` 和
`[ dihedrals ]`。

涉及 `standard_atom_deletions` 中已删除原子的条目删除；其余条目的 `funct`、显式参数及已有 comment 保持不变，
仅更新原子编号。

### topology-linked 非标准残基

从对应 `parameterized_topology.itp` 中提取同时满足以下条件的 `[ bonds ]`、`[ angles ]` 和 `[ dihedrals ]`：

1. 全部参与原子均存在于当前 `moleculetype`；
2. 至少一个参与原子属于当前 topology-linked 参数化对象中的非标准残基。

按当前 `[ atoms ] nr` 更新这些条目的全部原子编号。

在当前生成的 `.itp` 中，为每个 topology-linked 参数化正式结果单独设置补充区域。该区域分别写入从该正式结果
提取的 `[ bonds ]`、`[ angles ]` 和 `[ dihedrals ]`，与标准残基来源的相应条目分开组织，并在区域前注明
参数化正式结果来源。

### 独立非标准残基

采用对应 `parameterized_topology.itp` 中属于当前 `moleculetype` 的 `[ bonds ]`、`[ angles ]` 和
`[ dihedrals ]`，并按当前 `[ atoms ] nr` 更新原子编号。

### 经独立非标准参数化处理的 solvent / ion

采用对应 `parameterized_topology.itp` 中属于当前 `moleculetype` 的 `[ bonds ]`、`[ angles ]` 和
`[ dihedrals ]`，并按当前 `[ atoms ] nr` 更新原子编号。

## `[ pairs ]`

`[ pairs ]` 在 `[ bonds ]`、`[ angles ]` 和 `[ dihedrals ]` 完成整合后处理。

先保留当前标准残基和独立参数化来源中属于当前 `moleculetype`、且两个端点原子仍然存在的 `[ pairs ]` 条目，
并按当前 `[ atoms ] nr` 更新两个端点的编号。

对于 topology-linked 参数化正式结果，从对应 `parameterized_topology.itp` 中提取两个端点原子均存在于当前
`moleculetype` 的 `[ pairs ]` 条目。这里不要求端点中至少一个属于 topology-linked 非标准残基。

对提取出的条目更新两个端点的原子编号，并与当前 `moleculetype` 中已有的 `[ pairs ]` 进行比较；按 GROMACS
`[ pairs ]` 的实际语义判断重复并去除重复项。

在当前生成的 `.itp` 中，为每个 topology-linked 参数化正式结果单独设置 `[ pairs ]` 补充区域，集中写入该结果
经过上述处理后保留的 `[ pairs ]`，并在区域前注明参数化正式结果来源。

## 其它 `.itp` 项目

完成前述项目后，检查各来源 `.itp` 中实际存在的其它项目，包括但不限于：

```text
[ exclusions ]
[ constraints ]
[ settles ]
[ virtual_sites* ]
```

涉及原子编号的项目全部按照当前 `[ atoms ] nr` 更新编号。引用已删除或未进入当前 `moleculetype` 的原子时，
删除相应无效条目。

同时检查当前 `.itp` 实际引用的其它拓扑文件。若这些文件中的 restraint 或其它设置使用原子编号，按照当前
`[ atoms ] nr` 同步更新；引用已删除或未进入当前 `moleculetype` 的原子时，删除相应无效条目。

其余内容的保留或调整，由执行 Agent 根据对应 GROMACS 项目的实际语义和当前采用的来源拓扑定义判断。

## Position restraint

对于本次整合生成的每个 `<moleculetype name>.itp`，同时生成：

`posre_<moleculetype name>.itp`

并在对应主 `.itp` 中使用：

```text
#ifdef POSRES
#include "posre_<moleculetype name>.itp"
#endif
```

`posre_<moleculetype name>.itp` 使用 `[ position_restraints ]`，采用 harmonic position restraint
（`funct = 1`），仅对当前 `moleculetype` 中的重原子施加 restraint：

```text
fcx = 1000 kJ mol^-1 nm^-2
fcy = 1000 kJ mol^-1 nm^-2
fcz = 1000 kJ mol^-1 nm^-2
```

其中的原子编号必须与对应主 `.itp` 的 `[ atoms ] nr` 一致。

## 参数定义汇总与去重

从本次实际整合的来源 `.itp` 中收集以下参数定义：

```text
[ atomtypes ]
[ bondtypes ]
[ angletypes ]
[ dihedraltypes ]
[ pairtypes ]
[ nonbond_params ]
```

存在需要汇总的定义时，统一写入一个独立文件：

`parameters.itp`

不按参数类别拆分为多个文件。

是否属于同一参数项，由执行 Agent 按对应 GROMACS 项目的实际语义判断，不另行固化六套匹配规则。

先在收集到的来源定义之间处理：

- 同一参数项且定义相同：只启用一份，并保留其来源信息；
- 同一参数项但定义不同：视为冲突，向用户列明对应定义及来源，由用户决定，不按来源顺序自动覆盖。

再与当前体系实际采用的基础力场参数定义比较：

- 基础力场中不存在同一参数项：保留该本地定义；
- 基础力场中存在同一参数项且定义相同：不重复启用，在 `parameters.itp` 中以注释形式保留本地原定义，
  并注明其来源以及基础力场已经存在相同定义；
- 基础力场中存在同一参数项但定义不同：视为冲突，向用户列明对应定义及来源，由用户决定，不自动覆盖
  基础力场定义。

若本次没有需要汇总的上述参数定义，不为了文件对称生成空 `parameters.itp`。
