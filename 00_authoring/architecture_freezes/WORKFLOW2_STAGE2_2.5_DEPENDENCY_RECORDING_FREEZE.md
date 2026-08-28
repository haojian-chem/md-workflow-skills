# Workflow 2 Stage 2.5 dependency recording freeze

Status: CURRENT AUTHORING FREEZE

## Frozen rule

根据当前 Task Sheet 及其指定的前置工作项，确定本次拓扑整合实际使用的全部依赖文件，并按照 `references/results.md` 记录到当前拓扑整合结果中。依赖无法完整定位或存在未解决歧义时，不继续执行拓扑整合。

## Scope

本冻结项只固定拓扑整合开始时的依赖确定与结果记录要求。

具体需要记录哪些依赖文件、依赖项的数据结构与字段语义，由 topology integration and assembly 的 `references/results.md` 定义。

既有 2.5 architecture freeze 中关于 dependency / reuse / Runtime interface 的旧设计不作为本冻结项的解释依据。
