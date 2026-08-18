# Protonation assignment rules

本 reference 由 `1.7 Protein protonation assignment` 拥有，用于指导 Asp / Glu / His 的具体 protonation-state 判断。

# 1. Scientific scope and site semantics

当前处理对象：

- Asp；
- Glu；
- His。

Asp / Glu 对一个 carboxyl protonation state 做判断。

His 分别判断：

```text
ND1
NE2
```

两个 site assignments 对应：

```text
ND1 PROTONATED + NE2 DEPROTONATED
→ neutral His, ND1-protonated state

ND1 DEPROTONATED + NE2 PROTONATED
→ neutral His, NE2-protonated state

ND1 PROTONATED + NE2 PROTONATED
→ positively charged His

ND1 DEPROTONATED + NE2 DEPROTONATED
→ 不作为正常 final assignment；重新检查 evidence，仍不能闭合时向用户确认
```

当前 residue name 只是当前结构中的 naming state，不替代本次 protonation assignment。

# 2. Henderson–Hasselbalch assessment

PROPKA 只提供 predicted pKa。1.7 使用：

```text
Δ = predicted_pKa - target_pH
```

默认 `|Δ|` 阈值为 `1.0`：

```text
Δ > +1.0
→ PROTONATED

Δ < -1.0
→ DEPROTONATED

-1.0 ≤ Δ ≤ +1.0
→ BORDERLINE
```

如果当前项目或用户明确指定其他 `|Δ|` 阈值，则使用明确指定值，并在 `protonation_assignment_report.yaml` 的 `hh_delta_threshold` 中记录实际值。

对于 His，HH branch 的 `PROTONATED` 表示 imidazolium / positively charged side chain 倾向；`DEPROTONATED` 表示 neutral His side chain 倾向。Neutral His 的具体 ND1 / NE2 protonation placement 仍需要 site-level local-environment evidence。

如果 PROPKA 没有给出当前 residue 的可用 predicted pKa：

```text
propka_pka: null
henderson_hasselbalch_assessment:
  delta_pka_ph: null
  judgment: UNAVAILABLE
```

不得用默认溶液 pKa 补值。

# 3. Local chemical environment assessment

Local chemical environment 与 Henderson–Hasselbalch assessment 是平级 evidence branch，不是只有 HH borderline 时才触发的二级复核。

对当前 scope 内每个 residue 都检查实际局部化学环境；His 按 `ND1` / `NE2` 两个位点记录 site-level judgment。

## 3.1 Strong / direct evidence

以下 evidence 可以对具体 protonation state 形成强约束：

### Confirmed metal coordination

- Asp / Glu carboxylate O 作为明确 metal ligand 时，通常强支持 deprotonated carboxyl state；
- His 的 `ND1` 或 `NE2` 作为明确 metal donor 时，该 donor site 需要保持可供配位的 lone pair，因此支持该 site 为 `DEPROTONATED`；
- 不把单纯空间接近自动当作 confirmed coordination，使用当前任务已经确认的 coordination relation / chemistry。

### Confirmed covalent or special chemical state

如果已经确认的 covalent relation、chemical modification 或特殊活性位点化学明确要求某个 protonation state，则按该已确认化学关系形成相应 environment judgment。

### Reliable project-specific evidence

如果当前项目已有可靠实验、结构机制或明确用户决定指定某 residue / site 的 functional protonation state，可作为直接 evidence。

## 3.2 Supporting evidence

以下 evidence 通常作为支持性信息综合判断，不单独用简单距离阈值机械赋值：

### Salt bridge / charge compensation

- Asp / Glu 与明确正电中心形成合理 salt bridge 或存在稳定局部正电补偿时，支持 deprotonated carboxyl state；
- 只看到附近存在 Lys / Arg / metal 等对象而缺乏合理相互作用关系，不足以单独决定状态。

### Burial / desolvation

- Asp / Glu 深埋且负电荷缺乏合理局部补偿时，支持 protonated state；
- burial 只作为当前实际环境证据的一部分，不建立固定 buried-distance cutoff。

### Hydrogen-bond donor / acceptor geometry

根据当前结构中实际合理的 donor / acceptor role 判断：

- Asp / Glu carboxyl group 的 acceptor network 可支持 deprotonated state；
- 明确需要 carboxylic O-H donor 的局部网络可支持 protonated state；
- His `ND1` / `NE2` 明确承担 donor role 时支持该 site protonated；
- 明确承担 acceptor role 或 metal-donor role时支持该 site deprotonated。

普通近邻接触本身不足以形成确定 judgment。

### Solvent exposure

Solvent exposure 可作为辅助证据，但不单独决定 protonation state。

## 3.3 Environment judgment values

对每个记录 site，local-environment judgment 只使用：

```text
PROTONATED
DEPROTONATED
INCONCLUSIVE
```

`evidence` 应记录实际观察到并用于判断的信息；没有足以支持明确 site judgment 的 evidence 时使用 `INCONCLUSIVE`，不要为了填满报告伪造 evidence。

# 4. Combining parallel evidence

两类 evidence 不设置固定的“永远由 HH 覆盖 environment”或“永远由 environment 覆盖 HH”的优先级。

## 4.1 Asp / Glu

对 carboxyl state：

```text
HH definite + environment same definite
→ 接受一致 assignment

HH definite + environment INCONCLUSIVE
→ 采用 HH assignment

HH BORDERLINE + environment definite
→ 采用 environment assignment

HH UNAVAILABLE + environment definite
→ 采用 environment assignment

HH BORDERLINE / UNAVAILABLE + environment INCONCLUSIVE
→ evidence 不足，向用户确认

HH definite + environment opposite definite
→ 复核实际 evidence 与 relation；仍不能可靠解释冲突时向用户确认
```

## 4.2 His

HH branch 用于判断 positively charged His 与 neutral His 的总体倾向；local environment branch同时提供总体状态约束和 `ND1` / `NE2` site placement evidence。

默认解释：

```text
HH PROTONATED
→ 支持 ND1 + NE2 均 protonated 的 positively charged state

HH DEPROTONATED
→ 支持 neutral His；必须由 local environment / confirmed chemistry 确定或支持 ND1 / NE2 中哪个 site 保留 proton
```

如果 HH 为 `BORDERLINE` 或 `UNAVAILABLE`，local-environment evidence 可以在证据充分时确定总体 state 与 site placement。

如果 HH 与明确 local-environment chemistry 对总体 state 给出冲突结论，或 neutral His 的 ND1 / NE2 placement 无法可靠确定，则复核当前 evidence；仍不能闭合时向用户确认。

`ND1 DEPROTONATED + NE2 DEPROTONATED` 不作为正常 His final assignment。

# 5. Residue-name mapping

科学 assignment 完成后，根据当前 protein force field / protonation naming convention 将 state 映射到合法 residue name。

不要在本 reference 固定某一套 force-field residue names，也不要在目标 naming convention 无法表达当前 state 时自行发明 residue name。

如果 mapping 仍不明确，向用户确认 representation 后再写结构。
