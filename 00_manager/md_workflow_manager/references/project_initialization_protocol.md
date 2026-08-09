# 项目初始化事务协议

## 1. 适用范围

本协议仅用于 Manager 将入口状态判定为 `NEW` 后的基础初始化。

`NEW` 只是入口判定；初始化完成后的持久状态必须为：

```text
entry_state: RESUMABLE
```

初始化只建立项目管理骨架，不负责：

- 解析路线终点；
- 创建业务 route；
- 读取或调用 Workflow；
- 创建业务 task；
- 启动 Operation / Validator；
- 解析 PDB/mmCIF/AF3 CIF 内容；
- 创建初始化 snapshot。

## 2. NEW 启动条件

只有以下条件同时满足时自动初始化：

- Skill architecture root 已明确；
- MD project root 已明确；
- 没有可信可恢复状态；
- 项目为空或只有初始业务输入；
- 没有明显旧结构处理、拓扑、完整体系、模拟或管理产物；
- 没有目录所有权冲突；
- 不需要用户确认破坏性操作。

若已有明显业务/管理产物但无可信状态，不得通过初始化校验“顺便审计”，而应在入口阶段判为 `NEEDS_RECOVERY`。

## 3. 必需 capability

初始化只要求：

```text
INIT_CANDIDATE_VALIDATION
CONTROLLED_STATE_COMMIT
```

当前实现：

- `INIT_CANDIDATE_VALIDATION`：ACTIVE `runtime_schema_validator` 的受限 FAST candidate overlay；
- `CONTROLLED_STATE_COMMIT`：本协议第 6 节内建确定性提交路径；ACTIVE 状态事务 Tool 若以后提供，也可替代该路径。

capability 预检只确认实现、版本和必要路径可用，不执行项目级审计。

## 4. 初始化候选包

Manager 只生成两个状态候选：

```text
candidate project_state.yaml
candidate initial Workstream state
```

初始 Workstream 必须是未规划状态：

```yaml
current_position:
  workflow_name: null
  substep: null
  task_id: null
activity_status: IDLE
active_route_id: null
active_task_id: null
```

候选 project state：

- 持久 `entry_state` 设为 `RESUMABLE`；
- 索引首个 Workstream；
- Focus 可安全解析；
- 不包含尚未创建的 route/task/artifact/submission 引用。

## 5. INIT_CANDIDATE_VALIDATION

### 5.1 固定调用

NEW 初始化不再执行 FULL。固定使用：

```bash
python <skill_root>/05_tools/runtime_schema_validator/validate.py \
  --project-root <md_project_root> \
  --contracts-dir <skill_root>/03_contracts \
  --mode FAST \
  --changed <candidate_project_state> <candidate_workstream_state> \
  --logical-map <candidate_project_state>=00_project_state/project_state.yaml \
  --logical-map <candidate_workstream_state>=00_project_state/workstreams/<workstream_id>.yaml
```

该 invocation profile 称为 `INIT_CANDIDATE_VALIDATION`；它不是新的 validator CLI mode。

### 5.2 校验范围

只验证：

- 两个候选对象各自 schema；
- 两个候选对象的直接引用；
- candidate logical-path overlay 下的 project → Workstream state 路径关系；
- 候选 Workstream 中若意外出现 route/task/artifact/decision/submission 引用，其直接引用必须可解释，否则失败。

不验证：

- PDB/mmCIF 或其他业务文件内容；
- 全项目 route/task/artifact/decision/submission/event 历史；
- 未列入 `--changed` 的 runtime object；
- 路线范围或 Workflow 可用性。

若 project root 内出现旧 runtime/business 产物，应由入口判定处理，而不是扩大 INIT candidate gate。

### 5.3 重跑规则

- candidate 未变化且已有有效 PASS：不得重复验证；
- Tool 调用错误/空结果不算 PASS，修正 invocation 后可重跑；
- candidate 修改后必须重新验证；
- FAIL 不得通过改用 FULL、降低 gate 或 LLM 手工审计绕过。

R6 验证证据：

```text
04_evals/initialization_candidate_validation/VALIDATION.md
```

## 6. 受控提交

候选 PASS 后按固定顺序：

1. candidate 位于与目标相同文件系统中的受控临时位置；
2. PASS 前不得改写正式 `project_state.yaml` 或 Workstream state；
3. 检查同名冲突；如已有目标，准备 `.bak` 或等价恢复副本；
4. 完整写入并关闭候选文件；
5. 使用原子 rename/replace 提交；
6. 任一提交失败立即停止；
7. 未发生正式替换时返回 `BLOCKED`；
8. 已发生部分提交时进入 `NEEDS_RECOVERY`，保留候选、备份和失败证据。

该提交路径只处理管理状态，不复制、移动或修改业务输入。

## 7. 初始化事件与 lightweight verification

状态提交成功后：

1. 追加 `ENTRY_STATE_EVALUATED: NEW`；
2. 追加 `PROJECT_INITIALIZED`；
3. 做 lightweight post-commit verification；
4. 初始化结束。

post-commit 只确认：

- 正式 project/Workstream state 存在且可解析；
- project ID、Workstream ID、两个 root 与已验证 candidate 一致；
- `entry_state: RESUMABLE`；
- 正式文件 hash/确定性比较与 candidate 一致；
- 两个初始化事件成功追加且可定位；
- 无 candidate/backup 冲突信号。

post-commit 不再执行 FAST/FULL schema 扫描。发现提交不一致时进入 `NEEDS_RECOVERY`。

## 8. 初始化 barrier

在 `PROJECT_INITIALIZED` 已提交且 lightweight verification 通过前，禁止：

- 读取 Workflow 定义；
- route scope resolution；
- Workflow planning/execution；
- route record；
- subagent task；
- 前台业务 Agent；
- Operation / Validator。

初始化结束后才进入：

```text
PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
```

路线歧义、Workflow 未连接和后续业务输入问题不得追溯为初始化 blocker。

## 9. Snapshot

NEW 初始化不创建 snapshot。

首次权威 project state、初始 Workstream state、初始化事件以及 candidate/backup/失败证据已经构成恢复锚点；没有更早可信状态时复制 snapshot 不增加有效恢复信息。

## 10. 失败处理

### capability 缺失

返回 `BLOCKED`，当前 blocker 只列缺失 capability；后续 route/Workflow 问题列为 pending。

### candidate validation 失败

返回 `BLOCKED`；不提交正式状态、不写 `PROJECT_INITIALIZED`、不进入业务流程。

### 部分提交或 post-commit 异常

进入 `NEEDS_RECOVERY`；停止新的写入型 task；保留候选、备份、事件和失败证据；不得通过重复验证掩盖事务问题。
