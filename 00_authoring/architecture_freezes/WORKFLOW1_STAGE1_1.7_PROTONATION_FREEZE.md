# Workflow 1 / Stage 1.7 Protein protonation assignment architecture freeze

Status: **FROZEN AUTHORING REFERENCE — NOT AN ACTIVE SKILL**

## 0. 文档定位

本文件保存 `1.7 Protein protonation assignment` 已经讨论并敲定的设计事实，以及后续正式生成 Skill 时需要直接继承的细节。

它不是 `SKILL.md`，也不表示 1.7 已经获得正式 Skill generation / activation 许可。正式 Skill 生成时，应以本 freeze + 当时 current 的 1.6/1.8 接口 + authoring rules 为输入。

本文件迁移并保留此前误放入 active Skill 路径的 1.7 详细内容，同时合并保留历史 Operation / Validator 中的有效信息；不恢复旧 Workflow / Operation / Validator 角色分类。

Source preservation:

- former active pseudo-Skill: `01_structure_preparation/1.7_protein_protonation_assignment/SKILL.md`, blob `8e57488383663411fa996df1cd985c356fdb7d6c`
- historical operation source: `02_operations/protein_protonation_assignment/SKILL.md`, blob `632e03e6507a598dd9adab3ec6a4690c40afedda`
- historical validation source: `02_validators/protein_protonation_validator/SKILL.md`, blob `a7e2d4f24367837492953264f3472a4e0a934a64`

## 1. Purpose and boundary

1.7 的目标是在进入 Stage 2 前，确定蛋白质中需要显式区分的 protonation state，并把该决定落实为目标 force field 可识别的 residue naming。

1.7 决定的是：

```text
protonation state
→ target-force-field residue name
```

1.7 不负责：

- 标准残基最终加氢；
- 删除或补充重原子；
- 改变重原子坐标；
- 重新执行 1.6 completion/correction；
- Stage 2 topology generation。

标准残基最终 H 由 Stage 2 标准残基 topology generation 处理。

## 2. Required object / evidence

生成正式 1.7 Skill 时，至少应消费：

- 1.6 已验证的 `completed_structure.pdb`；
- 当前任务采用的蛋白质 force field，或明确的 protonation-state residue naming convention；
- 可执行 PROPKA；
- 必要时可读取当前结构局部化学环境；
- 必要时可读取上游 classification / relation 信息，尤其是配位、成键或其他会影响质子化状态的已确认关系。

## 3. Frozen assignment logic

执行逻辑冻结为：

1. 对当前结构中的蛋白质残基执行 PROPKA；
2. 对需要区分 protonation state 的残基，结合以下证据判断：
   - PROPKA 结果；
   - 当前局部化学环境；
   - 已确认的配位关系；
   - 已确认的成键关系；
   - 其他会影响 protonation state 的结构信息；
3. 将确定状态映射为目标 force field 对应的 residue name；
4. 在 PDB 中修改 residue name；
5. 不因 protonation assignment 增加最终 H、删除重原子或改变原子坐标。

PROPKA 是重要证据，不等于无需环境判断的机械命名器。对于明显受局部配位 / 成键 / 特殊环境影响的残基，必须结合实际结构环境解释。

无法仅凭 PROPKA 与结构环境形成可靠结论时，应保留歧义并向用户确认，不静默选择。

## 4. Reuse model to carry into Skill generation

已有 1.7 结果只有在以下条件均明确等价时才可自动复用：

- 输入结构相同；
- PROPKA 设置相同；
- 目标 force-field naming convention 相同；
- 所有影响结果的人工 protonation decisions 相同。

明确变化时重新执行；信息不足时由后续正式 Skill 按 Lightweight Runtime 的通用原则处理。

## 5. Validation boundary

Validation 属于 1.7 结果 owner，不需要恢复独立 Validator layer。

至少检查：

1. 报告中每个被赋值残基的最终 protonation state 与最终 residue name 一致；
2. 最终 residue name 可由目标 force field 正常识别；
3. 需要人工确认的 protonation decision 已解决；
4. 除允许的 residue-name 修改外，输入和输出 heavy-atom set、atom name、坐标与顺序没有非预期变化；
5. 1.7 没有生成最终氢原子。

任一 blocking 问题存在时，1.7 不能视作完成。Validation 不修改结构。

## 6. Frozen results / handoff

后续正式 Skill 的结果方向至少包括：

```text
protonation_assigned_structure.pdb
protonation_assignment_report.yaml
protonation_validation.md
```

`protonation_assignment_report.yaml` 至少应能定位：

- chain / residue；
- 原 residue name；
- PROPKA 结果；
- 局部环境判断；
- 最终 protonation state；
- 最终 residue name。

既有 execution-directory 约定为：

```text
01_structure_preparation/07_protein_protonation_assignment/<task_id>/
```

该路径是科研项目 execution directory，不是本仓库 Skill source directory。

## 7. Handoff to 1.8

1.8 消费已经落实 protonation-state residue naming 的当前重原子结构。

1.7 不建立 Stage 1 final atom order，也不做 final chain assignment；这些属于 1.8 的职责。

## 8. Skill-generation note

正式生成 1.7 Skill 时：

- 直接继承本 freeze 中 PROPKA + local-environment 的判定边界；
- 保留“只改 residue naming、不生成最终 H、不改变 heavy-atom structure”的硬边界；
- 不恢复旧 `Operation + Validator` 双层包装；
- 不因为模板需要而重新讨论已经冻结的 protonation assignment 逻辑；
- 只有实现层命令构造、报告细节、reference 拆分等尚未冻结内容，才在 authoring 阶段继续细化。
