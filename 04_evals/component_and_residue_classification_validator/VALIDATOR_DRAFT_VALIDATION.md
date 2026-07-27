# Component and residue classification v1 draft validation

## 状态

```text
DRAFT — synthetic executable validation passed; real-file and Manager integration pending
```

## 当前实现

- 6 个公开确定性入口（含 shared result wrapper）；
- 4 个内部解析模块；
- 10 个本地 schema；
- 严格大小写 project/Skill definitions；
- PDB/mmCIF/AF3 model scope；
- baseline classification、chain groups、missing residue observations；
- CCD local-first snapshot；
- RTP standard/terminal heavy-atom checks；
- possible covalent connection and metal coordination checks；
- final topology promotion and report rendering。

## 已执行

```text
python -m py_compile scripts/*.py
pytest -q
```

当前结果：

```text
8 passed
```

覆盖：

- schema meta-validation；
- single/multi model；
- registry classification；
- polymer/water/ion/repeated-small-molecule grouping；
- CCD specified-local-directory priority；
- altLoc heavy-atom skip；
- explicit HEM–CYS metal coordination and topology promotion；
- force-field terminal RTP heavy-atom missing checks；
- duplicate nonwater RTP template confirmation；
- strict case-sensitive residue definitions；
- local wrapper assembly with input STRUCTURE status preserved。

## 尚未验收

- 真实 RCSB PDB；
- 真实 RCSB mmCIF；
- 真实 AF3 CIF + input JSON/FASTA；
- remote CCD download and transient retry；
- large pair-result compression benchmark；
- ACTIVE FAST validation and Manager task closure；
- downstream 1.3 compatibility review。
