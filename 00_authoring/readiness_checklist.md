# 多窗口编写启动检查

只有以下项目全部通过，才能把业务 Skill 交给新网页窗口。

## 架构

- [ ] `layer_boundaries.md` 已冻结；
- [ ] `runtime_subagent_protocol.md` 已冻结；
- [ ] 明确 Workflow 不是 Agent；
- [ ] 明确任意时刻最多一个 MD 临时子 Agent；
- [ ] 明确网页窗口不是 Agent。

## Contracts

- [ ] `common_types.schema.yaml` 已冻结；
- [ ] `confirmation_item.schema.yaml` 已冻结；
- [ ] `workflow_decision.schema.yaml` 已冻结；
- [ ] `subagent_task.schema.yaml` 已冻结；
- [ ] `subagent_result.schema.yaml` 已冻结；
- [ ] `project_state.schema.yaml` 已冻结。

## 目标 Skill

- [ ] 层级已确认；
- [ ] 局部 contract 已确认；
- [ ] content map 已确认；
- [ ] 上下游接口无待决冲突；
- [ ] work order 已建立；
- [ ] `write_paths` 无重叠。

## 清理检查

- [ ] 未出现开发子 Agent 名称；
- [ ] 未将 Workflow 设为运行时执行主体；
- [ ] 未出现 MD 并行调度字段；
- [ ] 运行架构与多窗口编写规则未混写。
