# MD Workflow Agent Test Entry

Status: TEMPORARY TEST HELPER

`AGENTS.md` 只用于测试 / Agent 调用时定位需要加载的 main `SKILL.md`。

它不属于任何 Skill package，不是 Skill 规则 owner，也不能作为正式 Skill dependency / reference 已建立或真实执行中可达的依据。

测试时按当前职责加载对应 main Skill：

```text
Skill authoring / maintenance
→ 00_authoring/SKILL.md

Project task management / initial planning
→ 00_manager/SKILL.md

Scientific task execution
→ 当前实际负责该 Stage / Step / capability 的 main SKILL.md
```

需要确认当前 Scientific Skill 是否已正式生成、或定位 current entry 时读取：

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`

正式 Skill 的 reference / supporting Skill / Tool 依赖由对应 `SKILL.md` 自身建立，不由本文件补充。
