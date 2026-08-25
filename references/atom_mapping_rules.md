# Stage 1 final atom mapping 共享规则

本文件是 Stage 1 final heavy-atom mapping 的共享 runtime reference。当前由实际执行原子映射或其验证的 Skill 引用；不定义 Stage 2 的 mapping / provenance 语义。

## 1. 上游身份基准

进入 1.8 时，可用于稳定定位 residue 的上游身份为：

```text
component_id + residue_id
```

具体原子来自当前有效重原子结构，并以当前 `atom_name` 识别。

1.8 不要求存在贯穿此前 Stage 1 步骤的永久 `atom_id`、历史 atom table 或 source-serial lineage。需要解释当前结构变化时，读取当前结构及必要的上游正式结果；不反向构造一套历史原子身份系统。

## 2. 1.8 首次物化 Stage 1 正式逐重原子 map

1.8 根据：

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

- `component_id + residue_id` 保持 residue stable identity；
- `serial + atom_name` 定位 `stage1_final.pdb` 中当前 final atom；
- 不额外生成永久 `atom_id`；
- 不保存 `origin`、初始结构 `source_atom_serial` 或 completion provenance。

若当前 final heavy atom 是此前结构准备步骤新增的原子，它直接作为当前 final structure 中的实际原子进入 map，不要求为其补造初始结构中的 source atom identity。

## 3. 1.9 final atom-map validation

1.9 独立验证 `stage1_final.pdb` 与 `stage1_final_map.yaml` 的逐原子一一对应：

- final PDB 每个 `ATOM / HETATM` 原子在 map 中恰有一条记录；
- map 不包含 final PDB 中不存在的额外 atom record；
- 对应记录的 `serial + chain_id + resid + residue_name + atom_name` 与 final PDB 实际原子一致；
- 每条 map record 的 `component_id + residue_id` 能定位到当前 1.2 正式 residue。

1.9 不重建初始结构到 final structure 的 atom lineage，也不新增 atom identity。

## 4. Stage 1 边界

本规则只定义 Stage 1 final atom mapping：

```text
current Stage 1 heavy-atom structure
→ 1.8 stage1_final.pdb + stage1_final_map.yaml
→ 1.9 final PDB / final map validation
```

Stage 2 如何建立或消费自己的 atom mapping / provenance，由 Stage 2 自身设计与对应 Skill 决定，本文件不作规定。
