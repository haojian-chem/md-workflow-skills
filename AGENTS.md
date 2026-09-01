# MD Workflow Agent Test Entry

Status: TEMPORARY TEST HELPER

`AGENTS.md` 只用于测试 / Agent 调用时定位需要加载的 main `SKILL.md` 和 current shared communication reference。

它不属于任何 Skill package，不是 Skill 规则 owner，也不能取代正式 Skill / shared reference 的 authority。

测试时按当前职责加载对应 main Skill：

```text
Skill authoring / maintenance
→ 00_authoring/SKILL.md

Project task management / initial planning
→ 00_manager/SKILL.md

Scientific task execution
→ 当前实际负责该 Stage / Step / capability 的 main SKILL.md
→ references/user_communication_rules.md
```

其中 `references/user_communication_rules.md` 是执行智能体用户可见沟通的 current shared authority。执行测试中，确认问题、进度说明、异常说明和结果摘要都必须按该文件表达；不要因为当前 scientific Skill 内部使用英文接口字段或内部 identity，就把这些内部表达直接复制给用户。

需要确认当前 Scientific Skill 是否已正式生成、或定位 current entry 时读取：

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`

正式 Skill 的其它 reference / supporting Skill / Tool 依赖由对应 `SKILL.md` 自身建立，不由本文件补充。
