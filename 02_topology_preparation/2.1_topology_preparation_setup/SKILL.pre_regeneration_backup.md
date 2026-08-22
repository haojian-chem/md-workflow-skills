# 2.1 Topology preparation setup

## Purpose

2.1 确定当前体系进入 Stage 2 topology preparation 前所需的力场及参数定义来源，并根据当前体系对象确定后续处理环节。

2.1 完成后更新当前 Task Sheet，使实际需要执行的 2.2–2.5 工作项与当前体系一致。

## Input

2.1 读取：

- Stage 1 完成后的当前体系结构；
- 当前体系对象分类信息；
- 当前可用的力场及参数定义来源；
- 当前 Task Sheet；
- 项目级 `project_result_index.md` 中已登记的 2.2–2.5 正式结果。

## Execution

### 确定力场及参数定义来源

确认当前体系使用的力场及其它参数定义来源，并记录实际路径。

当使用多个力场或参数定义来源时，检查同一 `STANDARD_RESIDUE` 是否存在重复定义，并确定当前体系采用的定义来源。

### 判断已有 Stage 2 结果是否适用于当前体系

读取项目级 `project_result_index.md`，检查已有 2.2–2.5 正式结果是否可以用于当前体系。

判断条件：

- 2.2：来源结构一致，且使用相同力场；
- 2.3：使用同一个 `.mol2`，且参数生成方法一致；
- 2.4：使用同一个 `.mol2`，且参数生成方法一致；
- 2.5：合并使用的输入文件一致。

### 确定对象对应处理环节

根据当前体系对象确定后续处理环节：

- `STANDARD_RESIDUE` → 2.2；
- 需要共同参数化的非标准残基组合 → 2.3；
- 按 residue name 需要独立参数化的非标准残基 → 2.4；
- 已有完整 topology definition 的 `SOLVENT_COMPONENT` / `ION_COMPONENT` → 2.5；
- 缺少完整 topology definition 的 `SOLVENT_COMPONENT` / `ION_COMPONENT` → 2.4。

对于需要共同参数化的非标准残基组合，根据实际拓扑连接关系判断。残基之间存在 topology connection，或多个非标准残基与同一标准残基形成需要共同处理的拓扑关系时，可作为同一 2.3 处理项。

### 更新 Task Sheet

根据对象分配结果更新当前 Task Sheet：

- 记录 2.1 当前使用的力场及参数定义来源路径；
- 记录多力场情况下标准残基定义检查结果；
- 建立实际需要执行的 2.2、2.3、2.4、2.5 工作项；
- 标记已有正式结果可直接用于当前体系的工作项。

## Results

2.1 不生成独立报告，不登记 `project_result_index.md`。

2.1 的结果体现在更新后的 Task Sheet 中。

2.2–2.5 正式结果由对应处理环节登记到项目级索引。

## Completion criteria

2.1 完成条件：

- 当前体系使用的力场及参数定义来源已确定；
- 多来源定义检查已完成；
- 当前体系对象已完成处理环节分配；
- 已有 Stage 2 结果适用性判断已完成；
- Task Sheet 已更新。
