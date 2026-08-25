# MD Workflow 原子映射共享规则

本文件是 MD Workflow 中 Stage 1 → Stage 2 原子映射与 source provenance 的共享 runtime reference。凡相关 Skill 涉及 atom mapping、Stage 1 final atom identity 或 Stage 2 `source_atom_serial`，必须按本文件解释，不在各 Step 内建立可独立漂移的第二套规则。

## 1. 1.2 的原子身份边界

1.2 的稳定身份只建立到 residue 层：

```text
model
└── component_id
    └── residue_id
```

1.2 不建立或输出：

```text
atom_id
atom table
atom mapping file
source_atom_serial lineage
```

1.2 `topology_linked_checks[]` 中的具体原子使用：

```text
component_id + residue_id + atom_name
```

定位当前结构中的检查原子。这里的 `atom_name` 是当前结构原子名称，不是额外的稳定 atom identity。

需要回看 1.2 输入原子时，直接读取 1.1 / 1.2 对应 source structure，并结合 1.2 的 `component_id + residue_id`、当前原子名称和正式检查记录解释；不得为此在 1.2 再复制一套 atom table。

## 2. Stage 1 中间步骤不维护永久 atom ID 链

1.3–1.7 不要求共同维护贯穿 Stage 1 的永久 `atom_id`。

Stage 1 的结构演化由各步骤当前结构及正式结果表达，包括但不限于：

- 1.4 删除未保留的 alternate-conformation atoms；
- 1.6 补入缺失重原子或缺失 residue；
- 1.7 落实质子化相关 residue name 变化。

后续处理当前原子时，以当前结构为事实来源，并结合 `component_id + residue_id`、当前 `atom_name` 和必要的上游正式报告定位；不得要求删除或新增原子拥有贯穿 1.2–1.7 的历史 atom ID。

## 3. 1.8 首次物化 Stage 1 正式逐重原子 map

1.8 是 Stage 1 首次正式生成 atom-level map 的步骤。

输入基准：

```text
current valid heavy-atom structure
+ 1.3 target residue mapping
+ 1.2 classification_result.yaml
```

正式输出：

```text
stage1_final.pdb
stage1_final_map.yaml
```

`stage1_final_map.yaml` 中每个实际重原子保存：

```text
serial
chain_id
resid
residue_name
atom_name
component_id
residue_id
```

其中：

- `component_id + residue_id` 是稳定 residue identity；
- `serial + atom_name` 定位 `stage1_final.pdb` 中当前 final atom；
- 不额外生成永久 `atom_id`；
- 不保存 `origin`、初始结构 `source_atom_serial` 或 completion provenance。

1.6 新增的重原子直接作为 final structure 当前原子进入 map，不伪造其在初始结构中的 source atom identity。

## 4. 1.9 的 final atom-map validation

1.9 独立验证 `stage1_final.pdb` 与 `stage1_final_map.yaml` 的逐原子一一对应：

- final PDB 每个 `ATOM / HETATM` 原子在 map 中恰有一条记录；
- map 不包含 final PDB 中不存在的额外 atom record；
- 对应记录的 `serial + chain_id + resid + residue_name + atom_name` 与 final PDB 实际原子一致；
- 每条 map record 的 `component_id + residue_id` 能定位到当前 1.2 正式 residue。

1.9 不重建初始结构 → final structure 的 atom lineage，也不新增 atom identity。

## 5. Stage 2 source provenance

Stage 2 的 source provenance 从 Stage 1 final handoff 开始，不继续追踪 1.1 原始结构 atom serial。

Stage 2 统一 `*.map` 的基本方向为：

```text
generated/output atom → source provenance
```

对源自 Stage 1 final heavy-atom structure 的原子：

```text
origin: SOURCE
source_atom_serial: <对应 stage1_final.pdb serial>
```

该 `source_atom_serial` 必须能通过 `stage1_final_map.yaml` 定位到对应的：

```text
component_id + residue_id + atom_name
```

对 Stage 2 新增原子：

```text
origin: ADDED_H
source_atom_serial: null
```

或：

```text
origin: CAP
source_atom_serial: null
```

Stage 2 可以建立自己的 generated/output atom index，但不得反向修改 Stage 1 final atom identity。

## 6. 分段 handoff 原则

原子映射使用分段 handoff，不建立贯穿整个 MD Workflow 的永久 atom ID：

```text
1.1 / 1.2 source structure
→ residue-level stable identity
→ Stage 1 structure evolution
→ 1.8 stage1_final.pdb + stage1_final_map.yaml
→ Stage 2 SOURCE provenance = Stage 1 final serial
→ Stage 2 generated/output atom mapping
```

各 Skill 只维护自己拥有的结构处理或 map 物化；跨 Step / 跨 Stage 的 identity 与 provenance 语义以本文件为准。