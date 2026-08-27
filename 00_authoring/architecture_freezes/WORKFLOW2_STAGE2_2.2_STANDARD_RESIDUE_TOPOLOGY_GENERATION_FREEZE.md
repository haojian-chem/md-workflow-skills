# 2.2 Standard residue topology generation 冻结记录

Status: PARTIAL DETAIL FREEZE

本文件记录 2.2 已经确认的输入、标准残基结构提取、pdb2gmx 处理以及输出核验与 `.itp` 组织规则。

本次冻结只覆盖下述内容。`*.map` 构筑、reuse、results / 正式结果接口及其它尚未讨论内容不在本次冻结范围内，后续继续补充。

2.2 当前仍为 freeze-only；本文件不等于 active `SKILL.md`，也不表示已生成完整 2.2 Skill。

## 输入与处理范围

当前环节的处理范围由 Task Sheet 中对应工作项确定。

执行时至少读取：

- 当前 Task Sheet；
- 当前体系对应的上游结果中的 `stage1_final.pdb`；
- 当前体系对应的 `classification_result.yaml`；
- 当前体系已经确定使用的力场及其它参数定义来源。

`classification_result.yaml` 用于定位当前处理范围内的 `STANDARD_RESIDUE` 及其既有身份信息，
不重新进行残基分类。

## 构造标准残基输入结构

按照 Task Sheet 中对应工作项确定的处理范围，从 `stage1_final.pdb` 中取得该处理范围内的标准残基，
构造 pdb2gmx 输入 PDB。

构造过程中保留 `stage1_final.pdb` 中原有的 chain 组织和 `TER` 设置，
不重新划分 chain 或重新设置 `TER`。

## 生成标准残基全原子结构与拓扑

以提取的标准残基结构作为结构输入，使用当前体系已经确定使用的力场及其它参数定义来源执行 pdb2gmx。

默认使用 `-ignh`，忽略输入 PDB 中已有的氢原子，
由 pdb2gmx 根据当前采用的残基定义重新生成氢原子。

## 核验并整理 pdb2gmx 输出

pdb2gmx 完成后，核验其生成的标准残基全原子结构和拓扑。

至少检查：

1. pdb2gmx 正常结束；

2. 每条 chain 对应一个 GROMACS moleculetype；

3. 每条 chain 内的残基组成和顺序与 pdb2gmx 输入 PDB 中对应 chain 一致；

4. 各 chain 的端基是否被正确设置：
   - 蛋白质 chain：检查 N 端和 C 端；
   - 核酸 chain：检查 5′ 端和 3′ 端。

拓扑文件按一条 chain 一个独立 `.itp` 组织。

若当前只有一条 chain，且 pdb2gmx 将该 moleculetype 的完整分子拓扑直接写入 `.top`，
需将对应分子拓扑分离为独立 `.itp`，并使 `.top` 通过 `#include` 引用该 `.itp`。
