# Missing-heavy-atom completion

本 reference 只在 1.6 当前 repair set 含 missing heavy atom 时读取。

它定义 coordinate-template correspondence、shared-heavy-atom alignment、missing-atom coordinate transplant、必要时改按完整 residue completion 处理，以及局部 geometry requirements。Repair scope 仍由 `structure_completeness_report.yaml` 决定。

## 1. Coordinate template

可使用能够提供当前 residue 所需完整重原子坐标的 AF3 residue、CCD component coordinate template 或其它用户确认的可靠 coordinate reference。

AF3 residue 不能仅因为 residue name 相同就任意选取；当前 target residue 与 reference residue 的 correspondence 必须能够由当前 residue identity、局部结构上下文或已建立的 target/reference mapping 清楚定位。对于已经存在于 target 中的 residue，不要求仅为 missing-heavy-atom completion 额外建立整条 polymer-chain mapping。

CCD component 是 component-level template，不涉及在一条具体 AF3 chain 中选择“哪个同名 residue”的问题。

如果多个 coordinate templates 均可用，不按来源名义建立固定 `AF3 > CCD` 优先级；优先采用与当前 residue 已有局部几何相容、能够稳定定位缺失原子的 template。

## 2. Shared-heavy-atom correspondence

使用当前 residue 已存在的共同重原子建立 target ↔ reference atom correspondence。实际工作信息至少能够明确：

```yaml
shared_heavy_atoms:
  - target:
      chain_id: A
      resid: 125
      atom_name: CA
    reference:
      chain_id: B
      resid: 127
      atom_name: CA
```

以及待 transplant 的 missing atoms：

```yaml
transplant_atoms:
  - target:
      chain_id: A
      resid: 125
      residue_name: ARG
      atom_name: NH2
    reference:
      chain_id: B
      resid: 127
      residue_name: ARG
      atom_name: NH2
```

这些是 Agent 执行中需要追踪的信息模型，不要求固定生成某个 YAML 文件。

## 3. Alignment requirements

用于 rigid-body alignment 的 shared heavy atoms 至少需要：

```text
3 个 uniquely mapped、non-collinear shared heavy atoms
```

三个非共线点是确定 3D rigid transform 的最低几何条件，不等于只要达到 3 个点就自动说明 local fit 可靠。

Anchor 选择优先考虑与缺失原子局部成键/几何环境相关的共同重原子。不要在 side-chain completion 中机械地只使用 N / CA / C，而忽略能够约束当前 side-chain conformation 的局部共同原子。

- 恰好 3 个 shared heavy atoms：确认 mapping 唯一且非共线，并在 transplant 后加强 local-geometry validation；
- 4 个或以上 shared heavy atoms：可比较合理的局部 anchor subsets，确认 rigid transform 不对某个单一 atom subset 过度敏感；
- local geometry 对 missing atom placement 的意义高于追求一个跨 residue 的全局最低 RMSD。

不设置跨 residue / component 通用的 RMSD cutoff。

## 4. Insufficient atom-level anchors

如果当前 residue 不存在至少 3 个适合且非共线的 shared heavy atoms，不继续做 atom-level coordinate transplant。

该 residue 改按 `missing_residue_completion.md` 的完整 residue completion 方法处理；这不是另一套 completion method，只是当前 repair item 的处理方式调整。

此时：

- 当前 partial residue 的已有 atoms 不作为该 residue 自身的 atom-level alignment anchor；
- missing-residue method 使用 surrounding observed residues / 已建立的 reference correspondence 完成整个 residue；
- 如果它与相邻 missing residues 连续，可以作为同一连续 completion region 处理；
- `completion_report.yaml` 对应 `added_residues` record 记录：

```yaml
repair_adjustment: insufficient shared-heavy-atom anchors; treated as missing residue
```

## 5. Coordinate transplant

Rigid transform 确定后：

- 只 transplant `structure_completeness_report.yaml` 已列出的 missing heavy atoms；
- 保留当前 residue 中已有且有效的 heavy-atom coordinates；
- transplant 后的 atom 使用 target residue 自己的 chain ID、resid、residue name 和目标 atom name；
- reference chain ID、residue number 或 serial 只用于 reference coordinate lookup；
- 不在 1.6 添加最终 H。

如果 reference template 中存在其它 target 未列为 missing 的 atom，不因此追加到 transplant scope。

## 6. Geometry acceptance

每次 missing-heavy-atom transplant 后至少检查：

- 新增 atom 与当前 residue 已有 bonded/local atoms 的相对几何是否合理；
- shared-heavy-atom alignment 是否稳定，特别是在只使用最低 3 个 anchor 时；
- 新增 atom 是否造成明显 severe steric clash；
- 原有 valid heavy-atom coordinates 是否保持不变；
- 新增 atom identity 是否与 target residue 和 repair item 一致。

普通可由后续 minimization 释放的轻微 close contact 不自动等同于 severe clash。

不设置跨 residue / element 类型统一的 bond-length、angle、RMSD 或 clash threshold；使用当前化学连接与局部构象作为判断依据，并在需要时记录实际测量值作为 evidence。

## 7. Working evidence to retain

执行期间至少保留足以恢复和验证以下信息：

- 实际使用的 coordinate reference / component file 完整绝对路径；
- target residue ↔ reference residue correspondence；
- 实际使用的 shared-heavy-atom pairs；
- 实际 transplant 的 target ↔ reference atom correspondence；
- fit RMSD 或其它实际使用的 alignment stability evidence；
- transplant 后的关键 local-geometry evidence；
- 明显 clash / close-contact evidence；
- 如果改按 missing-residue 方法处理，能够说明 shared-heavy-atom anchor 不足的事实。

这些中间信息不要求采用固定文件名或 rigid schema，但必须足以支持 `completion_report.yaml` 与 `completion_validation.md` 的结论。
