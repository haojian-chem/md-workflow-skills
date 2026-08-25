# MD Workflow atom mapping handoff architecture freeze

Status: **FROZEN AUTHORING RECORD**

本文件拥有 MD Workflow 中从 Stage 1 到 Stage 2 的原子映射边界。它只规定跨 Step / 跨 Stage 必须保持一致的 atom identity / provenance 语义，不替代各 Step 自己的结构处理、mapping materialization 或 validation 规则。

## 1. 1.2 不建立 atom-level stable identity

1.2 的稳定身份层级止于：

```text
model
└── component_id
    └── residue_id
```

1.2 不生成：

```text
atom_id
atom table
atom mapping file
source_atom_serial lineage
```

`classification_result.yaml` 中 topology-linked 检查端点继续使用：

```text
component_id + residue_id + atom_name
```

定位当前检查原子；这里的 `atom_name` 是当前结构中的原子名称，不建立额外 atom identity。

需要回看 1.2 输入时，原始原子事实直接来自 1.1 / 1.2 所对应的 source structure，并结合 1.2 已物化的 residue identity 与检查记录解释；不为此在 1.2 再复制一份原子表。

## 2. Stage 1 不维护贯穿 1.2–1.7 的永久 atom ID 链

1.3–1.7 不因为后续需要原子映射而被要求共同维护一套持久 `atom_id`。

Stage 1 中可能发生的操作包括：

- 1.4 删除未保留的 alternate-conformation atoms；
- 1.6 补入缺失重原子或缺失 residue；
- 1.7 改变蛋白 residue name 以落实质子化状态。

这些变化由各自正式结构与报告表达。后续需要定位当前原子时，结合：

```text
current structure
+ component_id + residue_id
+ current atom_name
+ 必要的上游正式报告
```

完成，不要求为删除、新增或改写对象维护贯穿整个 Stage 1 的历史 atom ID。

## 3. 1.8 首次物化 Stage 1 正式逐重原子 map

1.8 是 Stage 1 首次正式 materialize atom-level map 的 owner。

它根据：

```text
current valid heavy-atom structure
+ 1.3 target residue mapping
+ 1.2 classification_result.yaml
```

生成：

```text
stage1_final.pdb
stage1_final_map.yaml
```

`stage1_final_map.yaml` 每个实际重原子只保存当前 Stage 1 final identity：

```text
serial
chain_id
resid
residue_name
atom_name
component_id
residue_id
```

其中 `component_id + residue_id` 提供稳定 residue identity；`serial + atom_name` 描述当前 final PDB 中的具体 atom。

1.8 不为 final atom 额外生成永久 `atom_id`，也不在 map 中保存：

```text
origin
source_atom_serial
completion provenance
```

若某 final heavy atom 是 1.6 新增原子，它直接作为当前 final structure 中的原子进入 `stage1_final_map.yaml`；不要求伪造其在初始结构中的 source atom identity。

## 4. 1.9 对 final PDB / final map 做逐原子一致性验证

1.9 必须独立确认：

- `stage1_final.pdb` 中每个 `ATOM / HETATM` 原子在 `stage1_final_map.yaml` 中恰有一条记录；
- map 不包含 final PDB 中不存在的额外 atom record；
- 对应记录的 `serial + chain_id + resid + residue_name + atom_name` 与 final PDB 实际原子一致；
- 每条 map record 的 `component_id + residue_id` 能定位到当前 1.2 正式结果中的 residue。

1.9 不重新构造原子历史 provenance，也不回溯判断该 final atom 是否来自初始结构或 1.6 completion。

## 5. Stage 2 的 source provenance 从 Stage 1 final handoff 开始

Stage 2 不继续追踪 1.1 原始结构中的 atom serial。

Stage 2 统一 `*.map` 中：

```text
generated/output atom → source provenance
```

对于 `origin: SOURCE` 的重原子：

```text
source_atom_serial = stage1_final.pdb 中该 source heavy atom 的 serial
```

该 serial 必须能够通过 `stage1_final_map.yaml` 定位到对应：

```text
component_id + residue_id + atom_name
```

对于 Stage 2 新增原子：

```text
origin: ADDED_H → source_atom_serial: null
origin: CAP     → source_atom_serial: null
```

Stage 2 可以建立自己的 generated/output atom index，但不得反向写回或重新定义 Stage 1 final atom identity。

## 6. 接口原则

原子映射采用分段 handoff，而不是一条贯穿整个 MD Workflow 的永久 atom ID：

```text
1.1 / 1.2 source structure
→ residue-level stable identity
→ Stage 1 structure evolution
→ 1.8 stage1_final.pdb + stage1_final_map.yaml
→ Stage 2 SOURCE provenance = Stage 1 final serial
→ Stage 2 generated/output atom mapping
```

这样既能可靠追踪后续 topology 输出中的 source heavy atoms，又不会因为 Stage 1 中删除 / 新增原子而强迫 1.2 建立不必要的原子身份系统。

## 7. Ownership

- 1.2：拥有 residue-level identity 与 topology-linked atom-name endpoint 记录；不拥有 atom map。
- 1.8：拥有 Stage 1 final heavy-atom map materialization。
- 1.9：拥有 Stage 1 final PDB / map 的逐原子一致性检查。
- Stage 2 main shared interface：拥有 Stage 2 `*.map` 的统一 generated/output → source provenance 语义。
- 2.2 / 2.3 / 2.4：按 Stage 2 shared interface 生成各自产物 map。
- 2.5：按同一接口消费并汇总 mapping。
