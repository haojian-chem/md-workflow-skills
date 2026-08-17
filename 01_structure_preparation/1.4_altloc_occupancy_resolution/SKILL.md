---
name: altloc_occupancy_resolution
description: 结构准备 1.4。对当前待处理结构中的 alternate conformation / altLoc 进行有依据的构象选择，删除未选构象并生成单一构象结构，同时记录选择及证据。
---

# Purpose

完成结构准备 `1.4 Alternate conformation / altLoc resolution`。

本 Skill 的职责是：识别当前结构中需要处理的 alternate conformations，结合结构记录与当前化学环境选择后续保留的构象，将该选择落实到结构文件，并留下可追溯的决策记录。

本步骤不负责缺失残基/缺失重原子补全、atom/residue naming 修正、质子化处理或几何优化。

# Object requirements

当前对象是前序流程交给 1.4 的待处理结构。正常预期为 PDB，并以 PDB `altLoc` 作为主要 alternate-conformation 表示。

如果实际输入格式与预期不同：

- 先提示格式偏差；
- 若能够可靠识别并映射与 `altLoc` 等价的 alternate-conformation 语义，可以继续使用本 Skill 的选择原则；
- 若无法可靠解释候选构象及其关系，不自行猜测，应向用户说明歧义并请求决定。

多个 target 分别处理；1.4 不自行把一个 target 拆成多个输出结构，也不重新合并已有 target。

# Execution rules

## 1. 识别需要处理的 alternate conformations

扫描当前结构中实际存在的 alternate-conformation 标记。

对普通 PDB `altLoc`：

- `altLoc` 为空的原子视为不参与该构象分支的 shared atoms；
- 同一局部构象中具有相同非空 `altLoc` ID 的相关 atoms 构成一个候选构象；
- 支持 A/B/C 等多个候选，不限制为两个构象；
- `altLoc` 字母本身不作为选择依据。

只有 partial occupancy、但不存在实际 alternate conformer 时，不把它强行解释为新的构象分支；保留当前坐标信息，并在必要时记录说明。

同一 atom identity 出现多个坐标但缺少可可靠解释的 alternate-conformation 标识时，不按普通 altLoc 静默处理。

## 2. 构造选择对象

普通情况默认以一个 residue 内彼此关联的 alternate atoms 作为一个整体构象选择对象。

必须保持以下原则：

- shared atoms 始终保留；
- 一个候选构象作为整体选择；
- 禁止逐 atom 混选不同 altLoc，从而人为拼接出不存在的 hybrid conformer；
- 候选构象的 atom set 不完全相同时，不因此自动判定原子更多的一方更优。

如果 alternate state 明显跨越多个 residues、ligand、cofactor 或 metal-center local environment，并且这些 alternate states 具有耦合关系，则应在完整局部关系下共同判断，而不是机械逐 residue 独立选择。

如果无法可靠判断多个 altLoc group 是否属于同一耦合构象，应保留该不确定性并向用户确认，而不是仅凭相同 A/B 字母建立关联。

如果 alternate states 涉及不同 chemical identity 或 connectivity，则不作为普通“同一原子集合的坐标 altLoc”静默处理；需要结合实际化学含义判断，必要时请求用户决定。

## 3. 选择保留构象

构象选择应综合使用当前可获得的证据。主要证据包括但不限于：

- occupancy；
- 当前局部化学环境；
- 与相邻残基的相互作用和构象关系；
- ligand / cofactor interaction；
- metal coordination；
- hydrogen-bond / electrostatic interaction；
- hydrophobic packing / aromatic stacking；
- steric compatibility；
- 用户已经明确给出的构象选择。

occupancy 是重要证据，但不是唯一自动判据。不得仅按“字母 A 优先”、文件中先出现者优先或人为固定阈值机械选择。

当 occupancy 与局部化学环境共同支持同一候选时，可直接选择该构象；当 occupancy 差异较小或局部有轻微不一致时，可以结合化学环境和其他可解释结构证据形成判断。

如果 occupancy 与化学环境明显冲突，应先检查这种冲突是否来自构象耦合、当前保留环境变化、异常 annotation 或其他可解释因素。只有在现有证据仍无法形成可靠选择时才请求用户决定。

不得仅因为某个候选 atom set 更完整、后续 repair 工作更少，就优先选择该构象。所选构象本身存在 missing atom 不阻止本步骤完成构象选择；缺失问题由其真正 owner 处理。

## 4. 用户确认

只有在现有证据不足以形成可靠选择时才请求用户确认，例如：

- 多个候选构象均有合理支持，无法形成可靠偏好；
- occupancy 与化学环境等关键证据明显冲突且无法解释；
- 跨 residue / ligand / metal-center 的 alternate-state coupling 无法可靠确定；
- alternate states 涉及不同 chemical identity / connectivity，现有信息不足以判断研究对象应保留哪一种；
- alternate-conformation annotation 本身异常，无法可靠恢复候选构象；
- 用户指定的构象与实际输入不一致或不存在。

向用户确认时应一次性给出候选构象、已有证据、主要冲突点和需要用户决定的问题。

## 5. 将选择落实到结构

只有在对应构象选择已经明确后才应用结构修改。

对每个已处理构象对象：

1. 保留 shared atoms；
2. 保留 selected conformer atoms；
3. 删除 unselected conformer atoms；
4. 清除 surviving selected atoms 的已解析 `altLoc` 标记；
5. 保留 surviving atoms 的原坐标；
6. 保留 surviving atoms 的原相对顺序；
7. 保留 retained atoms 原有 occupancy，不统一改写为 `1.00`；
8. 按最终写入顺序重新连续编号 PDB atom serial。

除上述构象处理所必需的修改外，不改变：

- chain identity；
- residue number / insertion code；
- residue name；
- atom name；
- surviving atom coordinates；
- surviving atom relative order。

1.4 不执行能量最小化、side-chain rotation、clash repair、metal geometry optimization 或其他坐标优化。化学环境用于选择已有构象，不用于在本步骤生成新的优化构象。

# Validation requirements

Validation 跟随 1.4 的正式结果，在同一 Skill 内完成，不另设独立 Validator。

## 1. 决策与实际结构一致

根据本次构象选择记录逐项确认：

- selected conformer atoms 已保留；
- unselected conformer atoms 已删除；
- shared atoms 已保留；
- 没有混合保留互斥候选而形成 hybrid conformer；
- 已处理位置不再残留未解决的 alternate conformer / altLoc。

## 2. 没有非预期结构修改

允许的主动修改仅包括：

- 删除未选构象 atoms；
- 清除已解析的 altLoc；
- atom serial 重编号。

除这些允许变化外，检查 surviving structure 未发生非预期的 identity、coordinate 或 relative-order 变化，也没有误删 shared / unrelated atoms。

## 3. 输出结构有效

确认：

- atom serial 唯一且连续；
- 输出结构能够被可靠读取并继续作为结构对象使用；
- 本次 altLoc 处理没有造成明显的重复 atom identity 或结构记录异常。

Validation 不重新检查 missing residue、missing heavy atom、force-field atom-set compatibility、protonation 或后续 repair 问题。

任一 blocking 检查失败时，本次 1.4 结果不能作为完成结果交接；应修正当前 1.4 处理本身的问题后重新检查。

# Official results

当前任务实际完成 1.4 后，正式业务结果包括：

```text
01_structure_preparation/04_altloc_occupancy_resolution/<task_id>/
├── altloc_resolution_report.yaml
└── structures/
    ├── target_001.pdb
    ├── target_002.pdb
    └── ...
```

每个输入 target 对应一个处理后的单一构象结构；输出文件继续使用对应 `target_id` 作为文件名，避免多个 target 之间发生文件名冲突。

## `altloc_resolution_report.yaml`

该文件是 1.4 的正式构象决策记录。至少记录：

- 当前 target identity；
- source PDB；
- generated PDB；
- 实际处理的构象对象；
- candidate conformers；
- selected conformer / altLoc；
- 实际采用的主要 evidence；
- 简短 decision rationale；
- 必要的 warning / special note。

对普通 residue-local altLoc，不要求复制完整 atom list。只有 partial-residue、跨 residue / ligand / metal-center 或 candidate atom set 明显不一致等复杂情况，才按实际需要补充 affected residues / atoms。

`source_pdb` 与 `generated_pdb` 必须记录**完整绝对路径**，不能只记录文件名或相对于当前 task directory 的相对路径。例如：

```yaml
targets:
  - target_id: target_001
    source_pdb: /absolute/path/to/project/01_structure_preparation/03_chain_and_residue_selection/<source_task_id>/structures/target_001.pdb
    generated_pdb: /absolute/path/to/project/01_structure_preparation/04_altloc_occupancy_resolution/<task_id>/structures/target_001.pdb
    resolved_groups:
      - scope:
          chain_id: A
          resid: 35
          residue_name: LEU
        candidates:
          - altloc: A
            occupancy_summary: "..."
          - altloc: B
            occupancy_summary: "..."
        selected_altloc: A
        evidence:
          - occupancy
          - local_chemical_environment
        rationale: "..."
```

这里的 YAML 结构用于说明最低信息要求，不建立额外 rigid schema；实际记录可按当前 case 的复杂度增加必要字段。

# Project result registration

完成正式结果后，在项目级正式结果检索文件：

```text
<project_root>/00_project_records/project_result_index.md
```

登记本次 `altloc_resolution_report.yaml`，至少写入：

- 该报告的完整绝对路径；
- 简明说明：该文件是 Stage 1.4 的正式 altLoc / alternate-conformation 决策记录，包含各 target 的源/生成结构定位、候选构象、最终选择及主要证据。

只登记路径与说明；`project_result_index.md` 的具体组织格式由项目级数据管理规则拥有，本 Skill 不复制或重定义其内部格式。

# Working directory

当前任务工作目录：

```text
<project_root>/01_structure_preparation/04_altloc_occupancy_resolution/<task_id>/
```
