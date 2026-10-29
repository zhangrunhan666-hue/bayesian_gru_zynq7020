# Skill Package

本目录是从本作品开发过程中沉淀的可复用经验，面向“ZYNQ + HLS + PS 应用”的板级加速项目。

| Skill | 适用场景 | 文件 |
|---|---|---|
| HLS AXI-Lite 上板排查 | IP 不启动、AXI 读挂起、AP_DONE 读不到 | `hls_axi_lite_bringup.md` |
| 大验证集外置 SD | BOOT.BIN 过大、DONE 不亮 | `externalize_large_testset.md` |
| MC Dropout 自适应 K | 需要不确定性/拒识的 PS 推理 | `mc_dropout_adaptive_k.md` |
| 板端/PC 黄金对比 | 量化部署后验证一致性 | `board_pc_golden_compare.md` |

每个 Skill 均给出：适用场景、使用方法、失效条件、来自哪些失败/观察。Skill 不绑定本题目，换模型或换板卡后仍可复用其中的检查顺序与脚本模板。
