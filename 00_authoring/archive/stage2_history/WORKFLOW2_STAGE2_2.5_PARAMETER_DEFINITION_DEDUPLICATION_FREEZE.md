# 2.5 Parameter-definition collection and deduplication

本 reference 只在 2.5 处理 parameter-level topology definitions 时读取。

目标是把 2.2–2.4 输入 `.itp` 中的六类 definitions 汇总到 **一个独立 `.itp`**，并避免与当前实际引用 force field 重复或冲突。

# 1. Scope

只处理以下六类：

```text
[ atomtypes ]
[ bondtypes ]
[ angletypes ]
[ dihedraltypes ]
[ pairtypes ]
[ nonbond_params ]
```

不得把它们分别拆成六个 `.itp`。

`[ defaults ]` 不属于本汇总规则；它由当前实际引用的 force-field topology hierarchy 管理，其来源由当前 Task Sheet 的 2.1 工作项记录。

# 2. Collection

扫描本次 2.5 实际使用的所有 2.2 / 2.3 / 2.4 `.itp`。

若六类 directive 中任一实际存在：

1. parse directive；
2. 保存 normalized definition；
3. 保存 provenance：source file、directive、原始顺序、原始 comment（可用时）；
4. 汇入一个 candidate definition set。

不因为某类通常位于 force-field files 就忽略输入 `.itp` 中实际存在的定义。

# 3. Two-level comparison model

去重必须区分：

```text
identity
vs
parameter definition
```

不得只比较整行文本，也不得只因为数值相同就合并不同 identity。

统一判定：

```text
same identity + same parsed definition
→ duplicate

same identity + different parsed definition
→ conflict

different identity + same values
→ not duplicate
```

# 4. Numeric normalization

参数比较使用 **parsed numeric value**，不使用原始字符串。

例如：

```text
1
1.0
1.000000
1.0e0
```

在同一字段语义下视为同一个数值。

不要引入任意 floating tolerance 去把真实不同参数合并。

推荐使用 decimal/lexical numeric normalization，使仅格式不同的数字相等，而 `1.000000` 与 `1.000001` 保持不同。

comments / whitespace 不参与 parameter equality，但 provenance comments 应尽量保留。

# 5. Identity keys

## 5.1 `[ atomtypes ]`

identity：

```text
atom type name
```

其它实际出现字段属于 definition，例如可选 bonded type / atomic number，以及 mass、charge、particle type、nonbonded parameters。

同名 atom type 的 definition 不同即为 conflict。

## 5.2 `[ bondtypes ]`

identity：

```text
canonical(atom_type_i, atom_type_j) + funct
```

二原子 bond identity 对正反顺序做 canonicalization。

## 5.3 `[ angletypes ]`

identity：

```text
canonical(atom_type_i, atom_type_j, atom_type_k) + funct
```

保持 center atom `j` 不变，只把：

```text
i-j-k
k-j-i
```

作为同一 canonical orientation。

## 5.4 `[ pairtypes ]`

identity 默认基于：

```text
canonical(atom_type_i, atom_type_j) + lookup function family
```

二原子 pair 对正反顺序做 canonicalization。

GROMACS 对普通 `[ pairs ]` function type 1/2 的 parameter lookup 不按两个完全独立的 pair-type namespace 处理，因此实现时不得仅凭 line-level `funct` 差异制造两个本应共享 lookup 的 identity；同时必须保留实际 function/parameter field semantics，遇到 free-energy/B-state 形式差异时不得静默合并。

若 parser 无法可靠解析该特殊形式，保守处理为 conflict/user review，而不是猜测。

## 5.5 `[ nonbond_params ]`

identity：

```text
canonical(atom_type_i, atom_type_j) + funct
```

二原子 cross-type nonbonded interaction 对正反顺序做 canonicalization。

## 5.6 `[ dihedraltypes ]`

identity 至少包含：

```text
atom-type lookup pattern
+
funct
```

必须保留 GROMACS 的实际 lookup 语义：

- 可能使用 4 atom types；
- 某些形式允许 2 atom types；
- `X` wildcard 是 lookup pattern 的一部分；
- 不同 wildcard specificity 不是因为数值相同就可强行合并；
- reverse orientation 只在 function/pattern 语义明确等价时做 canonicalization；
- 不得把 proper / improper 或不同 `funct` 混为同一 identity。

# 6. `dihedraltypes funct = 9`

`funct=9` 是特殊情况。

连续的 multiple parameter entries 可以共同定义同一 dihedral lookup pattern 的多个 potentials，因此不能按普通规则“same identity 只留一行”。

处理单位应为：

```text
one contiguous funct=9 multi-term block
```

规则：

```text
same lookup pattern + identical normalized multi-term block
→ duplicate block

same lookup pattern + different multi-term block
→ conflict
```

不得：

- 任意删掉 block 中一行；
- 把不同来源的连续性打散后再按单行去重；
- 因 multiplicity 不同就把其误判为重复行。

# 7. First dedup: 2.2–2.4 internal merge

对 candidate definition set 做第一轮 dedup。

## Exact duplicate

```text
same identity + same parsed definition
→ keep one active definition
→ merge provenance
```

## Conflict

```text
same identity + different parsed definition
→ do not choose by source order
→ do not choose by “later wins”
→ present all sources and definitions to user
```

用户决定前 consolidated parameter file 不得被视为 final。

# 8. Second dedup: against referenced force field

第一轮 merge 后，与本体系 **实际引用的 force-field parameter include tree** 比较。

必须比较真正生效的 parameter definitions，而不是只固定检查 `ffbonded.itp` / `ffnonbonded.itp` 两个文件名。

处理当前 final topology 的 include/preprocessor context：

- 跟踪实际 force-field includes；
- 只把已确认 active 的 definitions 当作第二轮 dedup 依据；
- 若 conditional include 是否生效无法确定，不得据此静默 comment out local definition。

## FF does not define identity

```text
local definition remains active
```

## Same identity + same definition in FF

本地汇总文件中：

```text
retain original/local definition as commented line(s)
```

不得物理删除。

推荐追加 provenance note，例如：

```text
; commented: already defined identically in referenced force field: <path>
```

这样既避免 active redefinition，又保留 2.2–2.4 参数来源痕迹。

## Same identity + different definition in FF

```text
conflict
→ do not silently override
→ do not silently comment out local definition
→ present to user
```

用户决定哪套 definition 应为 active 后再继续。

# 9. Output organization

最终只生成 **one consolidated parameter-definition `.itp`**，directive 顺序建议：

```text
[ atomtypes ]
[ bondtypes ]
[ angletypes ]
[ dihedraltypes ]
[ pairtypes ]
[ nonbond_params ]
```

不存在的 section 可以省略，不需要创建空 directive。

每个 active definition 尽量保留来源 comment/provenance；与 force field 完全重复的 definition 保留为 commented definition + note。

# 10. Include order

GROMACS topology parameter definitions 必须在 molecule-level entries 使用之前已经定义。

final topology 的 parameter-level include 顺序应满足：

```text
referenced force-field base / parameter includes
↓
consolidated local parameter-definition .itp
↓
final molecule .itp file(s)
↓
[ system ]
[ molecules ]
```

这样：

- force field 已有 identical definition 的 local copy 已被 comment out；
- local-only new atom/interaction types 在 molecule topology 使用前可见；
- unresolved same-identity/different-definition conflict 不依赖“last definition wins”偶然解决。

# 11. Conflict report minimum fields

每个 conflict 至少报告：

```text
directive
normalized identity
source A path + definition
source B path + definition
force-field source path（如适用）
why not safely deduplicable
required user decision
```

不允许仅输出“duplicate parameter error”而不指出具体 identity 和来源。

# 12. Implementation safety

在 deterministic parser/tool 尚未建立并验证前：

- 不使用正则字符串替换作为唯一 topology parser；
- 不按整行字符串简单 `sort | uniq`；
- 不依靠 GROMACS 的 later-definition overwrite 作为 merge algorithm；
- 不在真实 2.5 task 中临时修改共享 `05_tools/`。

若以后建立 deterministic Tool，必须为以下场景提供 tests：

- numeric formatting-only duplicate；
- same identity / different values；
- reversed bond/angle/pair identity；
- wildcard dihedral lookup；
- funct=9 multi-term block；
- identical FF definition comment-out；
- conflicting FF definition；
- conditional/inactive include 不应触发 false dedup。
