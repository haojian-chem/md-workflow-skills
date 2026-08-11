---
name: <workflow-skill-name>
description: <科研阶段边界、子环节关系和 Step→Skill 映射用途>。
---

# 目标

说明本 Workflow 要把什么类型的科研对象推进到什么阶段完成状态。

# 职责边界

Workflow 是阶段级科研规则与 Step 映射，不是 Agent，也不是 route/decision dispatcher。

不负责：

- 创建或修改 Task Sheet；
- 返回 route fragment / workflow decision；
- 维护 Workstream / active route / event；
- 执行具体 Operation / Validator；
- 定义具体 Step 的 reuse conditions；
- 复制 Step 的算法与详细科学规则；
- 为 Manager 判断某个 Step 是否适用于当前体系。

# 阶段目录

列出稳定 Step 基础目录，例如：

```text
<workflow_directory>/
├── <step_01_base_directory>/
├── <step_02_base_directory>/
└── ...
```

基础目录不是完成证据。

# Substep registry

每个 Step 至少声明：

```yaml
step_id:
name:
base_work_directory:
skills:
  operation:
  validator:
```

不在这里重复具体 Step 的输入、reuse、preflight、输出 schema、执行命令或科学适用性条件。

# 阶段内科学关系

按真正有用的上下游关系说明：

```text
上游 Step 的哪个正式结果
→ 下游 Step 如何消费
```

如果某个正式结果可能使后续尚未执行 Step 被增加、删除、替换或重排，只说明这种科学关系；具体判断由 Task Execution Agent 在执行时根据相关 Step Skill 和当前正式结果完成。

# 动态任务计划关系

Workflow 可以记录阶段内常见的计划调整关系，但不把它们编码成 Manager `conditional` 标记。

规则：

- Manager 只按用户任务范围和 planning index 生成初始计划；
- Manager 不根据体系科学特征判断 Step applicability；
- Task Execution Agent 在执行过程中依据当前证据直接调整尚未执行的未来 Step；
- 确认不需要且尚未执行的 Step 直接从 Task Sheet 删除；
- 必要的新 Step 可以加入 Task Sheet；
- 不生成 SKIP / route revision 对象。

# 复用边界

Workflow 不定义通用 reuse conditions。

每个 Step 开始时由 Task Execution Agent 读取当前 Step Skill，并按该 Skill 的 reuse conditions 判断。

# 阶段完成条件

明确什么实际科学验证结果代表本 Workflow 完成。

不得用：

- 目录存在；
- 文件名存在；
- 某 Step 曾经执行过；

替代真正的阶段完成条件。

# Legacy

以下不是 Lightweight Workflow 默认接口：

```text
Workstream
workflow_route_fragment
workflow_decision
active route
route revision
runtime task unit
```

# 自检

- [ ] 只拥有阶段级科学边界与 Step 映射；
- [ ] 未复制具体 Step 科学规则；
- [ ] 未创建 route / decision / Workstream 接口；
- [ ] 未把 Step applicability 写成 Manager conditional metadata；
- [ ] 计划调整关系只由执行证据触发；
- [ ] 最终完成条件来自真实验证结果。
