# Workflow 2 Stage 2 架构冻结与 2.5 linked `.itp` integration 讨论交接

## 0. 文档定位

本文件用于记录 Workflow 2 当前已经冻结的 Stage 2 架构，以及下一轮单独讨论 `2.5 Topology integration and assembly` 中 `TOPOLOGY_LINKED_NONSTANDARD` `.itp` integration 时必须继承的前提。

本文件是**设计冻结/讨论交接记录**，不是最终正式 Skill，也不替代后续 `01_workflows/`、planning index、content map 或 operation/validator 的正式落地。

当前状态：

- `2.1–2.6` 的步骤结构、主要职责、核心输入输出关系和关键边界：**冻结**；
- `2.5 linked .itp integration` 的逐 directive 科学规则：**尚未冻结，需单独讨论**；
- 核酸/DNA/RNA 的 2.3 截断细节：**尚未专项冻结**；
- 最终文件命名、schema、目录名：**尚未全部冻结**。

---

# 1. Stage 2 总体架构

Workflow 2 的目标是：从 Workflow 1 已完成结构识别、分类、选择、整理和重原子层面准备的结构出发，建立可用于后续体系构建的完整全原子 topology package，并在交给 Workflow 3 前完成 topology validation。

Stage 2 冻结为六个步骤：

1. `2.1 Parameterization environment and assignment`
2. `2.2 Standard residue topology generation`
3. `2.3 Topology-linked nonstandard parameterization`
4. `2.4 Independent nonstandard parameterization`
5. `2.5 Topology integration and assembly`
6. `2.6 Topology validation`

对象分类沿用 Workflow 1 / 1.2：

- `STANDARD_RESIDUE`
- `TOPOLOGY_LINKED_NONSTANDARD`
- `INDEPENDENT_NONSTANDARD`
- `SOLVENT_COMPONENT`
- `ION_COMPONENT`

`TOPOLOGY_LINKED_NONSTANDARD` 不等于“共价连接非标残基”。它表示该对象的 topology/parameterization 必须与另一个组件的 topology relation 联合处理，包括共价连接，也可包括被定义为 topology-forming 的配位关系。

---

# 2. 2.1 Parameterization environment and assignment

## 2.1 目标

2.1 只做两件事：

1. 建立当前体系后续使用的 parameterization environment；
2. 把实际对象分配给 2.2–2.5 的具体 topology acquisition / parameterization 路线。

2.1 不重新执行 1.2 分类，也不承担 Manager 式计划判断。

## 2.2 Parameterization environment

一个体系允许混合使用多个 force-field / parameter definition source，因此环境应抽象为：

```text
set of force-field / parameter definition sources
```

而不是单一 force-field path。

多个来源并存不自动构成冲突。只有同名不同定义、同一参数对象存在不兼容定义或其它真实 coverage 冲突时，才需要处理。

## 2.3 对象 assignment

### STANDARD_RESIDUE

全部标准残基整体分配给 2.2：

```text
all STANDARD_RESIDUE
→ 2.2
```

这里的“整体”只表示 2.1 的 assignment 粒度，不代表 2.2 只能运行一次 `pdb2gmx`。2.2 内部可根据实际软件/科学要求拆分 processing group。

### TOPOLOGY_LINKED_NONSTANDARD

每个具体 residue instance 单独进入 2.3。

### INDEPENDENT_NONSTANDARD

按 residue name/type 处理。同一 residue name 在 Stage 2 默认代表同一 topology type，只参数化一次。

若同名实例需要不同参数化，应先赋予不同 residue names，保证：

```text
one residue name → one topology definition
```

### ION_COMPONENT / SOLVENT_COMPONENT

若 parameterization environment 已提供完整 molecule topology definition，则不再经过 topology generation，2.5 直接使用。

若缺少完整定义，则按 independent nonstandard type 进入 2.4。

关键区分：

```text
STANDARD_RESIDUE
→ force field 提供 residue/template definition
→ 2.2 仍需为当前体系生成 molecule topology

FF-defined solvent / ion
→ force field 已有完整 topology include
→ 2.5 可直接使用
```

---

# 3. 2.2 Standard residue topology generation

## 3.1 目标

为当前体系全部 `STANDARD_RESIDUE` 生成实际的全原子 structure + topology。

输入：

- Workflow 1 的标准残基重原子结构；
- 2.1 的 parameterization environment / assignment。

## 3.2 processing group

2.1 将全部标准残基整体交给 2.2，但 2.2 内部允许按实际需要拆分 `pdb2gmx processing groups`。

明确否定把：

```text
one chain = one pdb2gmx run
```

作为默认规则。

## 3.3 补氢

2.2 负责 `STANDARD_RESIDUE` 的补氢。

Stage 2 不直接信任初始结构中的 H；标准部分的 all-atom 状态由 2.2 生成。

## 3.4 输出

2.2 的结构结果只包含 `STANDARD_RESIDUE` 部分。

主要输出类别：

```text
standard-only .gro
standard-only .top
standard molecule .itp file(s)
corresponding *.map
```

即使单链，也尽量把 molecule topology 规范化为 `.itp`，同时保留生成的 `.top` baseline。

---

# 4. 2.2–2.5 统一 `*.map` 规则

## 4.1 职责

`*.map` 只回答：

> 当前输出原子是谁、来自哪里。

它不承担：

- connectivity；
- bond 描述；
- topology-link 删除逻辑；
- linked-site chemical decision。

## 4.2 映射方向

固定为：

```text
generated/output atom
→ source provenance
```

## 4.3 字段

```yaml
output_atom_index:
output_atom_name:
output_residue_name:
output_residue_number:
origin: SOURCE | ADDED_H | CAP
source_atom_serial:
```

规则：

### SOURCE

`source_atom_serial` 必填，映射回 Workflow 1 源结构。

### ADDED_H

`source_atom_serial` 为空。

不额外记录该 H 连接到哪个 source atom；connectivity 从 `.itp [ bonds ]` 或 `.mol2` 读取。

### CAP

`source_atom_serial` 为空，表示 parameterization model 截断时引入的封端原子。

## 4.4 不加入的状态

不加入：

```text
DELETED_BY_LINK
```

删除信息不属于 map。

---

# 5. 2.3 Topology-linked nonstandard parameterization

## 5.1 处理单位

每个 `TOPOLOGY_LINKED_NONSTANDARD residue instance` 单独处理。

## 5.2 主要职责

2.3 负责：

- 确定 parameterization model 范围；
- 从 2.2 提取标准侧 all-atom fragment；
- 从 Workflow 1 提取 linked nonstandard 的 source atoms；
- 仅对 linked nonstandard 自身补氢；
- 判断 topology link 导致的标准侧多余原子；
- 添加 parameterization cap；
- 完成 DFT / RESP(2) / Sobtop；
- 建立 mapping；
- 向 2.5 输出 linked-site modification 信息。

2.3 不直接修改 2.2 baseline topology/structure。

## 5.3 标准侧结构来源

2.3 参数化模型中的 standard fragment 来自：

```text
2.2 all-atom structure
```

因此它同时包含：

- Workflow 1 已有的 standard source atoms；
- 2.2 新增的 standard H。

从 2.2 提取进 2.3 的标准侧原子，必须保持它们在 2.2 中的相对顺序。

## 5.4 补氢边界

2.3 只负责：

```text
TOPOLOGY_LINKED_NONSTANDARD hydrogenation
+
CAP atoms / capping hydrogens
```

不重新给 standard fragment 补氢。

## 5.5 standard-side deletion 判断

已冻结规则：

> 2.3 根据已确认 topology relation，判断 2.2 生成的标准残基中哪些新增原子与 linked 状态不兼容。

例如 `CYS-SG-HG` 在 linked 状态下若 `HG` 不应存在：

```text
2.3 parameterization model
→ remove HG
```

但 2.2 baseline 保持不变。

职责划分：

```text
2.3 → 判断 standard-side modification
2.5 → 在最终 topology / structure 中实际应用
```

## 5.6 蛋白截取规则

若 linked nonstandard `X` 与 standard residue `A` 相连：

1. 完整保留 `A`；
2. 向 `A-1 / A+1` 扩展；
3. 截取边界跨过肽键；
4. 尽量使最终截断发生在合适的 C–C 单键；
5. 边界 carbon 通过 H 封端，形成 methyl-like cap。

## 5.7 核酸/DNA/RNA

当前只冻结方向，不冻结全部细节：

- backbone boundary 位于 phosphodiester linkage；
- 倾向保留糖侧 `O3' / O5'`；
- 对对应 O 做 H capping。

需后续专项核对。

## 5.8 atom order 冻结点

完成以下工作后：

```text
structure extraction
+
linked nonstandard hydrogenation
+
standard-side deletion for parameterization model
+
capping
```

parameterization model 的 atom order 冻结。

之后：

```text
mol2
map
OPT
FREQ
SP
chg
Sobtop input/output
gro
itp
```

都必须保持明确一致的 atom-index 对应。

## 5.9 `mol2` / `gro`

`.mol2` 在参数化模型完成提取、补氢、封端并冻结 atom order 后生成。

`.gro` 可由 Sobtop 或 Agent/tool 生成，但必须满足：

```text
gro atom order
=
mol2 / itp / map atom order
```

## 5.10 DFT / charge 路线

当前主路线：

```text
prepared parameterization model
↓
OPT
↓
基于 optimized structure 一起生成 FREQ + SP task files
↓
FREQ / SP
↓
Multiwfn
↓
RESP / RESP2
↓
*.chg
↓
Sobtop
```

具体 level of theory、basis set、solvent model、RESP/RESP2 settings 不在 Workflow 架构层写死。

## 5.11 2.3 map

standard fragment 继承 2.2 map：

```text
SOURCE → 保持相同 source_atom_serial
ADDED_H → 继续为 ADDED_H
```

linked nonstandard source atoms：

```text
origin = SOURCE
source_atom_serial = Workflow 1 source serial
```

2.3 新增 H：

```text
origin = ADDED_H
```

cap：

```text
origin = CAP
```

已删除、不进入 parameterization model 的 standard-side atom 不写入 map。

## 5.12 输出

每个 linked instance：

```text
*.mol2
*.chg
*.itp
*.gro
*.map
```

`.top` 若实际生成且有复现/检查价值可保留，但当前不强制作为核心 official handoff。

另需 `linked-site modification information`，至少表达：

- target topology relation；
- standard-side target residue/atom；
- 需从 2.2 baseline 删除的 atom；
- linked-side 对应信息；
- 其它 2.5 必须执行的 linked-site modification。

具体 schema 尚未冻结。

---

# 6. 2.4 Independent nonstandard parameterization

## 6.1 处理单位

按 residue name / topology type 处理。

同一 residue name → one parameterization type。

## 6.2 主路线

```text
select parameterization source instance
↓
extract independent nonstandard
↓
hydrogenate
↓
freeze atom order
↓
mol2 + map
↓
OPT
↓
FREQ + SP
↓
Multiwfn
↓
RESP / RESP2
↓
chg
↓
Sobtop
↓
itp / gro
```

## 6.3 与 2.3 的区别

2.4：

- 不读取 2.2 standard fragment；
- 不涉及 standard-side modification；
- 不需要 CAP；
- 不处理 topology link；
- 不更新标准残基；
- 最终参数作为独立 moleculetype 使用。

## 6.4 多实例两层输出

假设：

```text
LIG × 12
```

type-level：

```text
LIG.mol2
LIG.chg
LIG.itp
```

system-instance-level：

```text
LIG_all.gro
LIG_all.map
```

即：

```text
mol2 / chg / itp
→ single molecule / type-level

gro / map
→ all current system instances
```

## 6.5 representative instance

- 单一实例：直接使用；
- 多个结构基本等价：选择 representative；
- 明显不同构象且选择可能影响参数化：执行阶段向用户确认；
- 若确实需要不同 topology：先改为不同 residue names，再作为不同 types。

---

# 7. 2.5 Topology integration and assembly

## 7.1 目标

将：

- 2.2 standard；
- 2.3 linked；
- 2.4 independent；
- FF-direct solvent/ion definitions

整合成一个 topology、coordinates、atom identity、molecule composition 全部一致的完整 all-atom topology package。

## 7.2 输入

### 2.2

```text
standard.gro
standard.top
standard *.itp
standard.map
```

### 2.3

每个 linked instance：

```text
linked.mol2
linked.chg
linked.itp
linked.gro
linked.map
linked-site modification information
```

### 2.4

```text
type-level:
mol2
chg
itp

system-instance-level:
gro
map
```

### FF-direct

2.1 已确认可直接使用的 solvent/ion topology definitions。

---

# 8. 2.5 global/type-level topology definitions

2.5 不能简化为“把所有 `.itp` 在 `.top` 中 `#include`”。

需要区分：

## 8.1 molecule-local directives

例如：

```text
[ atoms ]
[ bonds ]
[ pairs ]
[ angles ]
[ dihedrals ]
...
```

它们属于具体 moleculetype。

## 8.2 global/type-level parameter definitions

例如：

```text
[ atomtypes ]
[ bondtypes ]
[ angletypes ]
[ dihedraltypes ]
[ pairtypes ]
[ nonbond_params ]
...
```

对这类 definitions，2.5 需要：

```text
extract
↓
collect
↓
deduplicate
↓
conflict check
↓
write dedicated parameter-definition .itp
↓
include from final.top
```

去重规则：

```text
same name + same definition
→ deduplicate

same name + different definition
→ conflict; never silently choose

different name + same values
→ no forced merge
```

最终 dedicated parameter-definition `.itp` 的文件名/schema 尚未冻结。

---

# 9. 2.5 linked integration 已冻结的高层职责

对每个 2.3 linked instance，2.5 至少负责：

1. 应用 2.3 给出的 standard-side deletion；
2. 更新与 linked nonstandard 相连的 standard residue atomic charge；
3. 将 linked nonstandard topology 参数整合进 final moleculetype；
4. 建立必要的 cross-boundary bonded terms；
5. 删除因原子删除/topology replacement 已失效的旧 terms；
6. 保证最终 molecule total charge / topology 一致。

已冻结的重要边界：

> linked 状态下 standard residue 的 charge 更新属于 2.5 integration 职责。

以下内容**尚未冻结，必须在下一对话专项讨论**：

- 哪些 standard-side atoms 使用 2.3 charge；
- 2.3 parameterization model 中哪些 charge 迁入 final topology；
- boundary charge 如何处理；
- target total charge 如何约束；
- 2.3 `.itp` 各 directive 如何选择性迁移；
- 哪些 2.2 bonded terms 保留、删除、替换；
- cross-boundary bond/angle/dihedral/pair/exclusion 如何生成、迁移与放置。

---

# 10. final moleculetype 中 linked residue 的位置

当前冻结规则：

> 同一条链的 `STANDARD_RESIDUE` 与归属于该链的 `TOPOLOGY_LINKED_NONSTANDARD` 组成新的 final moleculetype。

linked nonstandard 不插在与其连接的 standard residue 后面。

例如：

```text
A1
A2
A3
A4
A5
```

`X` 与 `A2` 相连，`Y` 与 `A5` 相连。

final residue block order：

```text
A1
A2
A3
A4
A5
X
Y
```

而不是：

```text
A1
A2
X
A3
A4
A5
Y
```

file ordering 与 topology connectivity 分离。

---

# 11. 2.5 coordinate ownership

最终坐标组装采用统一 ownership 规则。

## 11.1 2.2 负责贡献

```text
all STANDARD_RESIDUE coordinates
```

但先应用 2.3 给出的 standard-side deletion information。

因此最终标准部分是：

```text
modified 2.2 all-atom structure
```

## 11.2 2.3 负责贡献

只纳入：

```text
TOPOLOGY_LINKED_NONSTANDARD 本身最终应存在的 atoms
```

不纳入：

```text
parameterization model 中的 standard fragment
CAP
```

## 11.3 2.4 负责贡献

纳入该 independent type 在当前体系中的全部实例，来自 all-instance `.gro/.map`。

## 11.4 FF-direct solvent/ions

若当前结构已有相应实例，则纳入实际 coordinates；topology definition 使用 2.1 指定的 FF definition。

---

# 12. 2.5 final all-atom order

Workflow 1 只提供：

```text
heavy-atom identity / heavy-atom order
```

不能直接提供 final all-atom order。

final all-atom order 必须联合：

```text
Workflow 1
+
2.2
+
2.3
+
2.4
```

构造。

## 12.1 第一层：object/residue order

Workflow 1 提供重原子层面的稳定 object identity / ordering backbone。

2.5 尽量维持该顺序，只做 topology organization 所需的块级调整。

对于“standard chain + linked nonstandard”：

```text
该链全部 STANDARD_RESIDUE
↓
属于该链的 TOPOLOGY_LINKED_NONSTANDARD
```

linked residue 之间尽量保持 Workflow 1 中已有的 component/object 顺序，而不是按 attachment site 重排。

## 12.2 第二层：对象内部 all-atom order

### STANDARD_RESIDUE

继承 2.2 all-atom order。

2.5 仅删除 2.3 已判定需要删除的 atom，其余相对顺序不改变：

```text
2.2 all-atom order
-
2.3 deletion targets
→ final standard residue order
```

### TOPOLOGY_LINKED_NONSTANDARD

来源于 2.3，只保留 linked nonstandard 本身：

```text
SOURCE heavy atoms
+
2.3 ADDED_H
```

去掉：

```text
standard fragment
CAP
```

剩余 atom 保持 2.3 内部相对顺序。

### INDEPENDENT_NONSTANDARD

各 instance 保持 2.4 all-instance structure 中的 all-atom order。

## 12.3 第三层：system-wide order

2.5 按 final moleculetype / molecule composition 组织上述 all-atom blocks。

核心原则：

> 2.5 以 Workflow 1 的 heavy-atom identity/order 为结构骨架，继承 2.2–2.4 对各自负责对象生成的 all-atom order，并按照 final topology organization 进行必要的块级组合和最小修改。

2.5 不具有“自由重排”权限。

---

# 13. 2.5 final map

2.5 生成：

```text
final.map
```

它不是重新猜测 mapping，而是：

```text
inherit / merge 2.2–2.4 maps
+
apply final reindexing
```

继续使用统一 map schema。

final structure 中：

```text
CAP count = 0
```

已删除 atom 不写入 final map。

---

# 14. 2.5 最终结果类别

至少包括：

```text
final_system.gro
final_system.top
final_system.map
```

以及 final `.top` 实际依赖、由 2.5 生成或修改的本地：

```text
*.itp
```

包括：

- integrated molecule `.itp`；
- independent molecule `.itp`；
- dedicated global/type-level parameter-definition `.itp`；
- 其它 final topology package 所需本地 definitions。

Stage 2 的最终科学结果应视为：

```text
final topology package
=
final.top
+
all required local itp
+
final.gro
+
final.map
```

---

# 15. 2.6 Topology validation

## 15.1 目标

2.6 不再构建 topology，只验证 2.5 输出的 topology package 是否已经可以作为 Workflow 3 的可靠输入。

2.6 不“顺手修 topology”。失败时回到对应上游步骤修正。

## 15.2 验证类别

### A. package 完整性

检查：

- 所有 `#include` 可解析；
- 不缺 `.itp`；
- `[ moleculetype ]` 定义完整；
- `[ molecules ]` 引用均有 definition；
- global/type-level definitions 已正确汇总与引用；
- 无同名不同参数的静默冲突。

### B. topology 内部一致性

检查：

- atom index；
- bonded-term atom references；
- 删除 atom 后无 dangling terms；
- atom types 均有 definition；
- linked-site modification 已全部应用；
- standard-side charge update 已应用；
- linked topology parameter 已进入 final topology；
- 无 CAP topology 残留。

### C. topology ↔ coordinate 一致性

至少：

```text
expanded topology atom count
=
final.gro atom count
=
final.map row count
```

并逐 atom 检查：

```text
expanded topology order
↔ final.gro
↔ final.map
```

不能只检查 atom count。

### D. final.map 完整性

SOURCE：

```text
source_atom_serial exists
```

ADDED_H：

```text
source_atom_serial empty
```

CAP：

```text
must be absent in final.map
```

非预期的一个 source atom 对应多个 final atom 应报错。

### E. charge/connectivity sanity

检查：

- moleculetype target charge；
- whole-system expected charge；
- linked integration 后 charge consistency；
- duplicate bond；
- invalid atom reference；
- missing expected topology relation；
- obvious invalid connectivity。

### F. GROMACS preprocessing

使用最小 validation `.mdp` 对：

```text
final.top + final.gro
```

执行 `gmx grompp` 类 preprocessing validation。

但：

```text
grompp success != full 2.6 pass
```

mapping、CAP 泄漏、linked modification 完整性等科研语义仍需独立检查。

## 15.3 通过条件

只有全部成立：

```text
topology package complete
+
global definitions consistent
+
moleculetype topology internally valid
+
linked modifications fully applied
+
topology atom sequence == final.gro atom sequence
+
final.map complete and consistent
+
charge/connectivity sanity checks pass
+
GROMACS preprocessing succeeds
```

才能认为：

```text
Workflow 2 topology package = validated
```

## 15.4 输出原则

2.6 不复制一套 `validated_final.top/gro`。

2.5 topology package 仍是正式科学结果；2.6 只新增 validation result / validation status。

---

# 16. Stage 2 当前明确否定的方案

除非后续出现新的科学依据，否则不再恢复：

- generic `special/custom parameter generation` Workflow step；
- 按参数复杂度给非标对象分路；
- covalent-only 的 2.3 定义；
- 单独新增 DFT preparation Step；
- 单独新增 full-structure hydrogenation Step；
- 2.3 直接修改 2.2 baseline；
- map 中加入 `DELETED_BY_LINK`；
- 为 `ADDED_H` 在 map 中增加 source anchor；
- 用 atom name/residue name 猜跨步骤 atom identity；
- 把 2.5 简化为若干 `#include`；
- 2.5 自由重排整个体系 atom order；
- linked residue 插在其连接的 standard residue 后；
- 2.6 自动修复 topology；
- 仅凭 `grompp` 成功判定 Stage 2 validation 通过。

---

# 17. Stage 2 冻结边界

## 17.1 已冻结

- 2.1–2.6 六步结构；
- 各步骤主要科学职责；
- 1.2 classification → 2.1 assignment；
- 2.2 standard topology generation 边界；
- 2.3 linked instance-level parameterization 边界；
- 2.4 type-level parameterization + all-instance structure 边界；
- `*.map` 的基本职责与字段；
- standard-side deletion：2.3 判断、2.5 执行；
- 2.5 global definition 汇总/去重职责；
- 2.5 standard-side charge update 职责；
- 2.5 coordinate ownership；
- 2.5 final all-atom order 的分层继承规则；
- linked residue 位于 standard residue block 之后；
- 2.6 validation boundary。

## 17.2 尚未冻结

- 最终目录名/base dir；
- 所有正式文件名；
- linked-site modification schema；
- dedicated global parameter `.itp` 的文件名/schema；
- 核酸/DNA/RNA 的详细 2.3 截断规则；
- **2.5 linked `.itp` integration 的具体科学算法**；
- standard-side charge replacement 的精确规则；
- 各 topology directive 的逐项迁移规则。

---

# 18. 下一对话：2.5 linked `.itp` integration 专项讨论指南

下一对话不重新设计 Stage 2 总体架构，只讨论 `TOPOLOGY_LINKED_NONSTANDARD` 的 final topology integration。

推荐按以下顺序推进。

## 18.1 `[ atoms ]` 与 standard-side charge update

先解决：

- linked nonstandard 自身 atoms 如何加入 final moleculetype；
- standard fragment 中哪些 atom parameter 只用于局部参数/charge reference；
- 哪些 standard atoms 继续采用 2.2 definition；
- 哪些 standard atoms 的 charge 由 2.3 更新；
- linked-side charge 哪些来自 2.3；
- 删除 atom 后 final `[ atoms ]` index 如何重编号。

## 18.2 standard-side charge 的科学规则

2.3 parameterization model：

```text
standard fragment
+
linked nonstandard
+
CAP
```

需要确定如何得到：

```text
standard residue charge update
+
linked nonstandard final charge
```

必须讨论：

- 更新范围：整个相连 standard residue 还是局部 atoms；
- A-1/A+1 fragment 是否参与 final charge 更新；
- CAP charge 如何排除/重分配；
- parameterization-model total charge 与 final molecule target charge 的关系；
- charge normalization / redistribution；
- 同一 chain 有多个 linked sites 时如何避免重复覆盖。

## 18.3 bonded terms 的迁移规则

逐类讨论：

```text
[ bonds ]
[ pairs ]
[ angles ]
[ dihedrals ]
...
```

对于：

- linked nonstandard 内部 term；
- standard fragment 内部 term；
- cross-boundary term；

分别确定：

```text
keep
remove
replace
merge
```

## 18.4 2.2 原有 bonded terms 的处理

需要明确：

- 哪些原有 bond 删除；
- 与删除 atom 相关的 angle/dihedral/pair 如何清理；
- 新 topology relation 是否使部分 standard terms 需要替换；
- 如何避免旧 term 和新 term 重复。

## 18.5 cross-boundary terms

需要明确 linked relation 产生的：

```text
bond
angle
dihedral
pair / exclusion（若需要）
```

如何从 2.3 parameterization model / topology 结果提取或构造。

跨 2.2 / 2.3 的 atom identity 应优先通过：

```text
2.2 map source_atom_serial
↔
2.3 map source_atom_serial
```

对齐，而不是按 atom name 猜测。

## 18.6 global/type-level definition extraction

若 2.3 `.itp` 中出现：

```text
[ atomtypes ]
[ bondtypes ]
[ angletypes ]
[ dihedraltypes ]
...
```

需要确定：

- 哪些 definitions 实际进入 final dedicated global parameter `.itp`；
- 如何判断 final system 是否真正使用某项 definition；
- dedup key；
- 同名不同值冲突；
- 与 2.2 / 2.4 / base force field definitions 冲突时如何处理。

## 18.7 final integrated moleculetype order

总体顺序已冻结：

```text
all STANDARD_RESIDUE of chain
↓
all TOPOLOGY_LINKED_NONSTANDARD assigned to that chain
```

下一对话只需进一步明确：

- 多个 linked residues 的精确排序；
- 一个 linked residue 有多个 topology relations 时是否影响顺序；
- cross-chain topology relation 如何组织；
- final `[ atoms ]` index 重编号实现。

## 18.8 2.5 integration validator

在进入 2.6 全局 validation 前，2.5 内部至少应检查：

- expected deleted atom absent；
- expected standard charge updated；
- expected linked atoms present；
- expected cross-boundary bonded terms present；
- no stale terms referencing deleted atoms；
- no duplicate/conflicting global definitions；
- integrated moleculetype target charge correct；
- topology atom order 可映射到 final coordinate assembly。

---

# 19. 新对话起始指令

新对话可直接读取本文件，并使用以下边界继续：

```text
Stage 2 架构已经冻结。
现在只讨论 2.5 Topology integration and assembly 中
TOPOLOGY_LINKED_NONSTANDARD 的 .itp integration 具体科学规则。

从 [ atoms ] 和 standard-side charge update 开始。
不要重新设计 2.1–2.6 架构；
不要改变已冻结的 map、coordinate ownership、
standard/link residue block ordering 和 final all-atom ordering 规则。
```
