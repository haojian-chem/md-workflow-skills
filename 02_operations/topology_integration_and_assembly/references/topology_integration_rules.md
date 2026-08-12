# 2.5 Topology integration rules

本 reference 只在 2.5 实际执行 molecule-level topology migration / linked-site integration 时读取。

它不重新定义 2.3 nonstandard unit，也不重新执行 parameterization。

# 1. Identity 与 mapping

跨 2.2 / 2.3 / 2.4 的 atom identity 只能使用已经确认的 map/provenance 与上游正式 modification information 对齐。

禁止仅凭：

```text
atom name
residue name
residue number
```

猜测跨步骤 atom identity。

统一 map 方向保持：

```text
generated/output atom → source provenance
```

2.5 生成 final map 时只做 map merge + final reindexing，不重新猜 mapping。

# 2. Nonstandard unit 语义

2.3 的处理对象是 topo-linked nonstandard **unit**。

一个 unit 可以包含一个或多个 nonstandard residues。

因此所有 2.5 规则中：

```text
current linked object
= current nonstandard unit U
```

GROMACS residue identity 仍然按 unit 内实际 residue 分别保存；unit 不取代 `resnr / residue`。

2.5 不重新给 unit 分 chain；它消费 Workflow 1 已确定的 chain assignment。若 unit 的 standard-side linked residues 全部属于同一条 standard chain，则该 unit 归入该 chain；若跨多条 standard chains，则 unit 使用 Workflow 1 已建立的独立 chain identity。后续 GROMACS `moleculetype` merge 不覆盖这些 chain identities。

# 3. Final moleculetype

## 3.1 单一已有 moleculetype

若 unit 只共价连接一个现有 standard moleculetype：

```text
standard moleculetype + U
→ same final moleculetype
```

## 3.2 多个已有 moleculetype

若同一个 unit 同时共价连接多个现有 standard moleculetype：

```text
all covalently connected standard components + U
→ one final moleculetype
```

原始 chain identity 不因此消失。

## 3.3 `nrexcl`

收集参与 final moleculetype 的来源 `nrexcl`：

- 只有一个值或多个来源值一致 → 使用该值；
- 存在多个不同值 → 汇总来源和值，交用户决定；
- 不自动多数表决，不按 include 顺序覆盖。

# 4. Pre-integration final atom / residue order

final all-atom order 与 canonical final atom index **必须在任何 molecule-level topology integration 之前冻结**。

先按 coordinate ownership 确定 final atom set：

- standard：来自 2.2 all-atom structure，并应用 confirmed standard-side deletions；
- topo-linked unit：只保留 unit 自身最终存在的 SOURCE + ADDED_H atoms；
- 2.3 parameterization standard fragment / CAP：不进入 final atom set；
- independent：来自 2.4 all-instance structure；
- FF-direct solvent/ions：使用当前体系实际保留实例。

然后按以下顺序建立 final all-atom order：

1. object/residue block order 以 Workflow 1 heavy-atom identity/order 为骨架；
2. standard residue 内部继承 2.2 all-atom order minus deletions；
3. nonstandard unit 内部保留 2.3 final-retained atoms 的相对顺序；unit 内不同 residues 仍分别保留 identity；
4. independent instances 继承 2.4 all-instance order；
5. linked nonstandard block 不按 attachment-site 紧邻插入 standard residue，而是在所属 standard residue block 之后按上游 object order 组织；
6. 只做 final moleculetype organization 所需的块级组合，不自由重排。

在该顺序冻结时同步生成：

```text
canonical final atom index
final_system.map
source/local atom → final atom index mapping
```

后续所有 `[ atoms ]` / bonded-term remapping 与 `final_system.gro` 均消费这同一套 canonical final index；不得在 topology integration 或 coordinate writing 时另建第二套编号。

# 5. `[ atoms ]` integration

GROMACS `[ atoms ]` 字段：

```text
nr type resnr residue atom cgnr charge mass
```

2.2 / 2.3 `.itp [ atoms ]` 是 final atom property source，不是 final atom-entry template。

## 5.1 Standard atoms

standard atom properties 以 2.2 为 baseline：

- `nr`：使用已冻结的 canonical final atom index；
- `cgnr`：固定 `cgnr = final nr`；
- `resnr`：按 final residue organization 调整；
- `residue`：迁移对应 residue name；
- `atom`：迁移对应 atom name；
- `type`：默认迁移 2.2 type，仅 attachment-site atom 进入 applicability review；
- `charge`：先迁移 2.2 charge，随后对 `S_mod + U` 做 charge modification；
- `mass`：迁移对应 mass/definition。

standard atom name 包括 attachment-site atom name 不因 linkage 自动更名。

standard `[ atoms ]` comment：

- 2.2 原有 comment → 迁移；
- 2.2 没有 comment → 不主动给 standard residue 新增 comment。

## 5.2 Nonstandard unit atoms

一个 unit 内可能包含多个 nonstandard residues。

只写入 unit 自身最终存在的 atoms：

```text
SOURCE atoms
+
U 自身 ADDED_H
```

排除：

```text
2.3 parameterization standard fragment
CAP
```

剩余 atom 保持 2.3 内部相对顺序。

每个 constituent residue 保持自己的 residue identity；不得因为属于一个 unit 就合并成同一个 `resnr`。

对每个 unit 主动加入识别 comment，例如：

```text
; topo-linked nonstandard unit: U001
```

unit 内 residue identity 仍由实际 `[ atoms ] residue/resnr` 表达。

# 6. Standard-side deletion mechanical cleanup

顺序固定：

```text
final atom set/order/index 已冻结
↓
write/remap standard topology
↓
apply all confirmed standard-side atom deletions
↓
mechanically clean every reference to deleted atoms
↓
write topo-linked nonstandard content
```

mechanical cleanup 至少覆盖所有已存在的 molecule-level atom-reference directives，例如：

```text
[ atoms ]
[ bonds ]
[ pairs ]
[ angles ]
[ dihedrals ]
[ exclusions ]
[ constraints ]
[ virtual_sites* ]
[ settles ]
...
```

任何 entry 只要引用 deleted atom，就不能保留。

因此“standard topology 保持不变”的准确语义是：

> 除 canonical final index remapping 和 confirmed atom deletion 引起的 mechanical cleanup 外，standard topology entry 的其它内容保持不变。

# 7. Standard attachment-site atom type review

只 review standard-side **attachment-site atom** 的 atom type，不重新给整个 standard fragment/type system 赋型。

每个 attachment-site atom 分为：

```text
APPLICABLE
NOT_APPLICABLE
UNRESOLVED
```

## APPLICABLE

旧 atom type 在 linked chemical state 仍适用：

```text
keep old type
```

## NOT_APPLICABLE / UNRESOLVED

不得自动发明 replacement type，也不得把 Sobtop/generic type 批量复制给 standard residue。

向用户提供：

- target atom；
- old type；
- old vs linked-state chemical environment；
- neighbors / connectivity / bond order / coordination / hybridization / chemical role / formal charge（相关时）；
- old type 为什么不再适用或为什么证据不足；
- replacement type 需要满足的 chemical characteristics。

用户确认 replacement type 后再继续。

# 8. Charge modification

## 8.1 Scope

统一记为：

```text
S_mod + U
```

其中：

- `U`：当前 topo-linked nonstandard unit 中全部最终保留 nonstandard atoms；
- `S_mod`：当前 unit 对应的全部需要实际修改 charge 的 standard residues。

attachment residue 必须进入 `S_mod`。

若一个 unit 有多个 attachment sites，应联合处理其 standard-side modification scope。

例如：

```text
site 1 uses A-1 / A / A+1
site 2 uses B-1 / B / B+1
B+1 = A-1
```

则共享并位于联合连接区域的 residue `B+1(A-1)` 与 attachment residues `B`、`A` 一起进入 charge modification scope。

仅作为外围 parameterization context / CAP context、但不属于最终 modification scope 的 standard residue 不修改 final charge。

## 8.2 Mapping

- 使用 2.3 map 定位 2.3 charge source；
- 使用已经冻结的 final map 定位 final topology replacement target；
- 不建立新的 charge-specific mapping scheme。

## 8.3 RESP

对 `S_mod + U`：

1. 使用体系信息给出的 `Q_expected`；
2. 运行 unconstrained RESP；
3. 运行 total-charge constrained RESP，约束 `S_mod + U = Q_expected`；
4. final topology 使用 constrained result；
5. unconstrained result 只用于 QC/control；
6. 不做 posthoc CAP redistribution / normalization。

记录：

```text
Q_expected
Q_unconstrained
DeltaQ_unconstrained
Q_constrained
DeltaQ_constrained
MAE
RMSE
L_inf
```

## 8.4 RESP2

若使用 RESP2：

- constraint 在 RESP2 所依赖的每一次 RESP fitting 中直接施加；
- 不增加 separate post-mixing RESP2 charge constraint；
- 不做 post-mixing normalization；
- QC 仍比较 constrained / unconstrained output。

`Q_expected` 来自体系信息，2.5 不重新推断 chemical charge state。

# 9. `[ bonds ] / [ angles ] / [ dihedrals ]`

## 9.1 Standard baseline

2.2 standard bonded topology 全部保留：

- atom indices 映射到 canonical final atom index；
- confirmed deletion cleanup 删除失效 terms；
- 其它 fields / funct / explicit parameters / comments 保持不变。

## 9.2 2.3 term inclusion

对当前 unit U 的 2.3 `[ bonds ] / [ angles ] / [ dihedrals ]`，统一规则：

```text
all participating atoms are in final moleculetype
AND
at least one participating atom belongs to U
→ include
```

这同时覆盖：

- U 内单一 residue 内部 term；
- U 内不同 nonstandard residues 之间 term；
- standard ↔ U cross-boundary term。

standard-only 2.3 term 不迁入，因为 standard baseline 已由 2.2 提供。

CAP/non-final atom 参与的 term 不迁入。

proper 与 improper 都按相同 atom-membership 规则处理；不根据本 Step 自行重新解释 dihedral chemical class。

## 9.3 Placement

顺序固定为：

```text
entire standard bonded topology
↓
comment marking topo-linked nonstandard unit terms
↓
U-derived included terms
```

不是在每个 standard residue/module 后分别插入 linked terms。

# 10. `[ pairs ]`

`[ pairs ]` 不使用上一节“至少一个 atom 属于 U”的规则。

对 2.3 pair：

```text
both endpoints map into final moleculetype
→ map to canonical final atom indices
→ canonical pair dedup
→ if not already present, include
```

不得要求 pair endpoint 中至少一个属于 U。

原因是一个跨 linked region 的 1–4 topology path 可以经过 U，但 pair entry 本身两个 endpoint 都是 standard atoms。

因此 standard–standard pair 也可能必须从 2.3 补入。

# 11. `[ exclusions ]`

当前暂定为低频、用户决策型规则：

```text
collect from 2.2 / 2.3 / 2.4
↓
map all atom references to canonical final indices
↓
place under owning final moleculetype
↓
deduplicate
↓
if any selection/conflict remains, present to user
```

不在 2.5 自动推导新的复杂 exclusion policy。

# 12. Other molecule-level directives

其它实际出现的 molecule-level directives 纳入 2.5，而不是默认 unsupported。

主要操作：

```text
atom index remapping
+
ownership placement
+
mechanical cleanup of deleted/CAP/non-final references
```

例如：

```text
[ constraints ]
[ settles ]
[ virtual_sites* ]
...
```

若某 directive 存在超出机械 remapping/cleanup 的特殊科学语义且无法唯一处理，向用户确认，不静默猜测。

# 13. Multiple-unit overlap

正常情况下，实质共同耦合的 linked nonstandard region 应在 2.3 被定义为一个 unit。

若 2.5 发现不同 units 在以下任一方面出现实质 overlap：

- same standard-side charge modification target；
- same attachment chemistry；
- conflicting/overlapping deletion；
- overlapping linked-site modification ownership；

则：

```text
do not auto-merge 2.3 results
→ ask user
→ recommend merging them into one nonstandard unit and rerunning 2.3
```

# 14. Coordinates 与 final map

## Final map timing

`final_system.map` 在 molecule-level topology integration **之前**，与 final all-atom order / canonical final atom index 同时生成。

```text
merge 2.2–2.4 maps
+
apply final atom filtering/deletions
+
apply final reindexing
→ final_system.map
```

后续不再次生成第二份 final map。

final map 中：

```text
CAP count = 0
```

deleted atom 不写入 final map。

## Coordinate writing

最终 `.gro` 只是在 topology integration 之后，按已经冻结的 final all-atom order 写出 coordinates：

- Standard：坐标来自 2.2 all-atom structure，应用 confirmed standard-side deletions；
- Topo-linked unit：只贡献 unit 自身最终 SOURCE + ADDED_H atoms；不贡献 2.3 standard parameterization fragment / CAP；
- Independent：使用 2.4 all-instance structure/map；
- FF-direct solvent/ions：当前结构中实际存在实例贡献 coordinates。

coordinate writing 不得改变 canonical final index/order，也不重新生成 map。

# 15. 2.5 assembly completeness gate

完成前机械确认：

- final atom set/order/index 在 topology integration 前已冻结；
- every final atom index resolves；
- no deleted atom reference；
- no CAP/non-final atom reference；
- no stale 2.2/2.3/2.4 atom index；
- 每个 final moleculetype `.itp` 使用 canonical final index；
- final map numbering matches final topology numbering；
- final `.gro` 使用同一 canonical final order/index；
- final moleculetype ownership determined；
- all blocking user decisions resolved；
- final package file set explicit。

这些检查只证明 assembly 已完成；完整 topology correctness 交给 2.6。
