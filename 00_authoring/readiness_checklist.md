# 多窗口编写启动检查

只有以下项目全部通过，才能把业务 Skill 交给新网页窗口。

## 架构

- [ ] `layer_boundaries.md` 已读取；
- [ ] `runtime_subagent_protocol.md` 已读取；
- [ ] 明确 Workflow 是可复用 Skill，不是 Agent；
- [ ] 明确 Workstream 是项目中的具体工作分支；
- [ ] 明确任意时刻最多一个前台 MD 临时子 Agent；
- [ ] 明确多个外部 tmux/调度任务可以并存；
- [ ] 明确网页窗口不是 Agent。

## Shared contracts

- [ ] 已读取 `03_contracts/README.md`；
- [ ] 目标 Skill 所需 schema 已列入 work order；
- [ ] 若使用 task unit，已覆盖 `OPERATION | VALIDATOR | OPERATION_WITH_VALIDATOR` 中适用模式；
- [ ] Operation 与 Validator 的返回字段保持分离；
- [ ] 项目状态与 Workstream 状态未混为一个唯一当前 Workflow；
- [ ] 外部任务终态包含 `FINISHED_UNVERIFIED` 核验步骤；
- [ ] 业务 Skill 不直接写项目状态或记录目录。

## 目标 Skill

- [ ] 层级已确认；
- [ ] 最近邻职责边界已确认；
- [ ] 局部 contract 已确认；
- [ ] content map 已确认；
- [ ] 上下游接口无待决冲突；
- [ ] work order 已建立；
- [ ] inventory 状态允许启动；
- [ ] `write_paths` 无重叠；
- [ ] `forbidden_paths` 包含不允许修改的共享路径。

## 项目文件

- [ ] 已读取 `AGENTS.md`；
- [ ] 已读取 `00_authoring/SYNC_STATUS.md`；
- [ ] 已读取 `00_authoring/skill_inventory.yaml`；
- [ ] 已读取 `00_authoring/file_ownership.yaml`；
- [ ] 已读取目标 content map；
- [ ] 已读取对应 work order。

## 清理检查

- [ ] 未出现开发子 Agent 名称或配置；
- [ ] 未将 Workflow 设为运行时执行主体；
- [ ] 未出现多个前台 MD 子 Agent；
- [ ] 未将外部作业并存误写为 Agent 并行；
- [ ] 未复制共享 contract；
- [ ] 运行架构与多窗口编写规则未混写。
