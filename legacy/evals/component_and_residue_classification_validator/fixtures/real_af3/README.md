# Real AlphaFold Server acceptance fixtures

本目录保存用户提供的两套真实 AlphaFold Server template-free 输出，用于 component/residue classification v1.2 正式验收：

- `fold_1bk0_ipns_fe_template_free`：chain A protein + chain B FE；
- `fold_1dz9_p450cam_hem_template_free`：chain A protein + chain B HEM。

原始 `model_0.cif` 以 `xz+base64` 文本分片保存，原因是仓库连接器不直接接收上传 ZIP 中的二进制文件。测试流程必须：

1. 按 `fixture_manifest.yaml` 顺序合并分片；
2. 核验每片长度；
3. Base64 解码并 xz 解压；
4. 核验原始模型 size 与 SHA-256；
5. 恢复原始 `job_request.json` 字节并核验 size 与 SHA-256；
6. 使用公开 `classify_structure.py` 执行真实验收。

分片和文本换行仅属于仓库传输层，不改变用户上传科学输入的身份。不得降低或删除原始 SHA-256 gate。

AlphaFold Server 输出的使用受 `terms_of_use.md` 及 CIF 文件头部所声明条款约束。
