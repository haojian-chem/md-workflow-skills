# Project design references

Status: CURRENT

本目录保存 `00_authoring/SKILL.md` 在需要项目级背景时按需读取的设计资料。

这里的文件不是新的 Skill 入口，也不重新定义具体业务 Skill 的内部规则。

当前文件：

```text
MD_WORKFLOW_MASTER_PLAN.md
lightweight_runtime_v2_spec.md
```

职责：

- `MD_WORKFLOW_MASTER_PLAN.md`：只保存顶层阶段编号、各 Stage catalog、建设状态和 current authority 入口；
- `lightweight_runtime_v2_spec.md`：只保存跨 Stage 的 Lightweight Runtime 通用架构；
- 具体 Stage 科学/执行规则由对应 current `SKILL.md` / references 拥有；
- 已冻结的 Stage 架构记录位于 `../architecture_freezes/`。

不再单独维护 current `SYNC_STATUS.md`。阶段建设状态与待完成工作统一由 `MD_WORKFLOW_MASTER_PLAN.md` 记录，避免两份状态文件同步维护。
