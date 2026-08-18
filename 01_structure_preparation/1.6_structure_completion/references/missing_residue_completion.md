# Missing-residue completion

本 reference 只在 1.6 当前 repair set 含 missing residue，或某个原 missing-heavy-atom item 已明确需要按 missing-residue 方法处理时读取。

它定义 missing-residue coordinate completion 的 correspondence、local alignment、reference comparison、coordinate transplant 和局部 geometry requirements。Repair scope 仍由 `structure_completeness_report.yaml` 决定。

## 1. Reference basis

missing-residue completion 主要使用与当前 target 对应的完整 AF3 structure 作为 coordinate reference；用户提供的其它明确对应的完整结构也可以在科学上合适时使用。

Reference 用于提供坐标，不改变 target 已确定的 sequence、residue identity 或 repair range。

如果 completion region 在 reference 中与 target sequence / residue identity 不一致，该 reference 不能直接用于该 region 的 coordinate transplant。

## 2. Full polymer-chain residue correspondence

在使用 AF3 坐标补全某条 polymer chain 的 missing residue 前，先为**包含该 missing region 的整个 target polymer chain**建立完整 residue-level correspondence。

这里的 polymer chain 指 sequence-bearing polymer residues，不等于当前 PDB 显示在同一 chain ID 下的所有 component。仅因 topology link 或结构组织而与 polymer 同 chain 显示的 HEM、ligand 或其它 nonstandard component，不要求为了完成普通 polymer missing region 而强行纳入该 mapping；只有当前补全实际需要它们时才另外建立 correspondence。

Mapping 至少应明确以下逻辑字段：

```yaml
residue_mapping:
  - target:
      chain_id: A
      resid: 1
      residue_name: MET
    reference:
      chain_id: B
      resid: 5
      residue_name: MET
```

要求：

- mapping 覆盖该 target polymer chain 的完整 residue sequence，包括当前缺失位置；
- target / reference 的 chain ID 与 residue number 不要求数值相同；
- correspondence 依据完整 sequence context 与 residue identity 建立，而不是先找一个局部几何相似片段再反推身份；
- reference numbering 只用于定位 reference coordinates，最终结构始终使用 target 自己的 chain ID、resid、residue name 与顺序；
- 如果 mapping 存在不能消除的歧义，不继续 coordinate transplant。

完整 polymer-chain mapping 是 identity correspondence，不要求对整条 chain 做全局结构叠合。

## 3. Local alignment data

建立完整 residue correspondence 后，再从 mapping 中选择当前 completion region 的局部 observed anchors。

实际用于 rigid-body alignment 的信息至少能够明确：

```yaml
alignment_atoms:
  - target:
      chain_id: A
      resid: 96
      atom_name: CA
    reference:
      chain_id: B
      resid: 100
      atom_name: CA
```

以及本次真正需要 transplant 的 residues：

```yaml
transplant_residues:
  - target:
      chain_id: A
      resid: 98
      residue_name: GLY
    reference:
      chain_id: B
      resid: 102
      residue_name: GLY
```

这些是 Agent 执行中需要追踪的信息模型，不要求固定生成某个 YAML 文件。实际 atom selection 可以根据 polymer type 和局部结构选择可靠、共同存在的 heavy atoms；不为所有体系预设唯一 atom-name list。

## 4. Internal missing region

对于两侧都有 observed polymer residues 的 internal missing region：

1. 从缺失区两侧最近的 mapped observed residues 开始建立 bilateral local anchor；
2. 两侧 anchor 必须共同决定**一个 rigid-body transform**；
3. 不分别拟合 left / right 后再拼接 missing segment；
4. 如果最近 anchor 不足以给出稳定、几何一致的 transform，按序向两侧逐步扩大 local anchor；
5. 优先采用能够稳定满足两侧约束的最小 bilateral anchor，而不是为了降低某个 RMSD 任意挑选更远 residue；
6. 如果扩大 anchor 后一侧持续改善而另一侧持续恶化，或始终不能形成稳定的统一 transform，应认为当前 reference 的局部构象与 target 不兼容，不继续通过扩大区域强行平均。

Anchor expansion 不预设固定 N residues。停止扩展时应同时考虑：

- 两侧都能得到合理局部叠合；
- 再增加一层邻近 anchor 不会实质改变 transform；
- completion region 两端的 junction geometry 合理；
- 没有暴露出当前 reference 与 target 的系统性局部不兼容。

不设置跨体系统一的 RMSD cutoff。RMSD 或等价 fit measure 用作 alignment evidence，需要结合 anchor composition 与局部 geometry 判断。

## 5. Terminal missing region

如果 missing region 位于 polymer chain 端部，只有一侧存在 observed anchor：

1. 完整 polymer-chain residue correspondence 仍然是前置要求；
2. 从距离 missing region 最近的 observed residue 开始建立 one-sided local anchor；
3. 必要时沿 observed chain 向内逐步扩大；
4. 采用能够给出稳定 transform 的最小 one-sided anchor；
5. transplant 仅限目标 terminal missing residues。

Terminal completion 不人为构造不存在的 bilateral constraint。由于只有一侧几何约束，validation 中应保留相应 warning，并加强 junction geometry、local conformation 与 clash 检查；one-sided anchor 本身不自动构成 failure。

## 6. Coordinate transplant

Alignment 确定后：

- 只 transplant repair scope 中缺失 residues 所需的 heavy-atom coordinates；
- 不用 reference coordinates 替换 completion region 之外已有且有效的 target atoms；
- 新增 residue 使用 target mapping 中已确定的 chain ID、resid、residue name 与顺序；
- 不把 AF3 / reference 的 chain ID、residue number 或 serial 直接写入 target；
- 1.6 不补最终 H。

如果一个原 missing-heavy-atom item 因 atom-level anchor 不满足要求而改按 missing-residue 方法处理，则当前 partial residue 的已有 atoms 不再作为该 residue 自身的 atom-level alignment anchor；对该 residue 按完整 residue completion 处理。若它与相邻 missing residues 连续，可作为同一个连续 completion region 一并处理。

## 7. Multiple reference structures

如果用户提供多个与同一 target 对应的 AF3 reference：

- 使用同一 target polymer-chain correspondence basis；
- 对同一 completion region 使用可比较的 mapped local anchors；
- 主要比较 local fit stability、junction geometry、明显 steric clash 和与 target 局部构象的兼容性；
- 可把 reference 的 local confidence information 作为辅助选择因素；
- 高 confidence 不自动胜出，低 local confidence 也不自动淘汰。

不建立固定综合评分公式，也不使用统一 confidence cutoff。

单一 reference 的 completion region 如果 local confidence 明显偏低，应在 validation 中给出 warning，而不是仅凭 confidence 自动判 FAIL。

## 8. Geometry acceptance

Coordinate transplant 后至少检查：

- internal region 的两侧 junction 或 terminal region 的单侧 junction 是否具有合理 polymer connectivity / local geometry；
- 新增 residues 与周围 observed structure 是否存在明显 severe steric clash；
- 新增 residue identity 与 target mapping 一致；
- completion region 外已有 target coordinates 没有被无理由替换；
- internal region 的最终坐标确实来自同一个 bilateral transform；
- terminal region 的 one-sided alignment 在合理 anchor expansion 下稳定。

普通可在后续 minimization 中释放的轻微 close contact 不自动等同于 severe clash。这里不设置跨体系固定的 bond-length、angle、RMSD 或 clash numerical threshold。

## 9. Working evidence to retain

执行期间至少保留足以恢复和验证以下信息：

- 实际使用的 reference structure 完整绝对路径；
- 当前 target polymer chain 的完整 residue-level mapping；
- 本次实际使用的 alignment atom pairs / anchor residues；
- completion / transplant residues 的 target ↔ reference correspondence；
- fit RMSD 或其它实际使用的 alignment stability evidence；
- internal bilateral 或 terminal one-sided junction geometry evidence；
- 发现的明显 clash / close-contact evidence；
- reference local-confidence warning（如有）；
- 多 reference 情况下最终选择所依据的局部比较信息。

这些中间信息不要求采用固定文件名或 rigid schema，但必须足以支持 `completion_report.yaml` 与 `completion_validation.md` 的结论。
