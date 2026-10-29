# 3.3.5 提交内容对照清单

项目：`bayesian_gru_zynq7020`  
依据：2026 FPGA 赛道选题指南 3.3.5

## 一、3.3.5.1 工程包

| 要求 | 当前文件 | 状态 |
|---|---|---|
| 完整工程与源码（HLS/PS/Vivado/Python） | `src/hls/`、`src/vitis/`、`src/vivado/`、`src/python/`、`src/vivado/project/ps7020.xpr` | ✅ |
| 仿真或验证结果 | `sim/README.md`、`sim/gru_mv_csim.log`、板端/PC 对比 | ✅ HLS C 仿真 0 errors；无 RTL testbench |
| 综合与实现报告 | `build/csynth.rpt`、`build/impl_utilization.rpt`、`build/timing_summary.rpt`、`build/clock_utilization.rpt` | ✅ |
| 上板工程、运行脚本、实测输出 | `board/BOOT.BIN`、`data/CLIPS.BIN`、`board/uart_output.txt`、`board/uart_output.png`、`data/pc_reference.csv` | ✅ |
| 可复现构建脚本 | `build/build_steps.md`、`build/boot.bif`、`build/make_boot.ps1`、`build/build_app.ps1` | ✅ 一键脚本已实测 |

## 二、3.3.5.2 技能包

`skill/` 已包含：

```text
skill/README.md
skill/hls_axi_lite_bringup.md
skill/externalize_large_testset.md
skill/mc_dropout_adaptive_k.md
skill/board_pc_golden_compare.md
```

每项含适用场景、使用方法、失效条件、证据来源，不绑定本题目。

- 状态：✅ 已有 4 个通用 Skill
- 加分项：PYNQ 通用 Skill **未提供**（本作品不是 PYNQ 框架）

## 三、3.3.5.3 设计报告

| 要求 | 当前材料 | 状态 |
|---|---|---|
| 选题背景与创新点 | `report/design_report.docx` 第一部分 | ✅ |
| 设计原理与功能框图 | 第二部分，图 2-1/2-2 | ✅ |
| 软硬件划分依据与接口设计 | 2.1/2.3，AXI-Lite 0x43C00000 | ✅ |
| 优化过程与前后对比表 | 1.4/3.3/4.2 | ⚠️ 建议再加一张“优化前后”汇总表 |
| 大模型协作记录 | `report/llm_collaboration_record.docx`（3 页） | ✅ 已导出，原始界面截图可另附 |
| 技能包提炼过程 | `skill/` + 文档中的说明 | ✅ |
| 复现说明 | `build/build_steps.md`、`board/README.md` | ✅ |

## 四、3.3.5.4 推荐目录结构

```text
bayesian_gru_zynq7020/
├── README.md
├── LICENSE
├── src/
│   ├── hls/
│   ├── vitis/
│   └── vivado/
├── sim/
├── build/
│   ├── boot.bif
│   ├── fsbl.elf
│   ├── system_wrapper.bit
│   ├── app.elf
│   ├── csynth.rpt
│   └── impl_utilization.rpt
├── board/
│   ├── BOOT.BIN
│   ├── README.md
│   └── uart_output.txt
├── data/
│   ├── CLIPS.BIN
│   └── README.md
├── skill/
└── report/
```

- 目录名/文件名全部英文，符合 3.3.5.4。
- 中文仅出现在正文内容中。

## 五、3.3.5.5 评测指标与权重

| 评测项 | 权重 | 本项目对应材料 |
|---|---|---|
| 创新性与应用价值 | 30 | PS+PL GRU、自适应 K、边缘手势/拒识 |
| 性能与资源优化效果 | 20 | 3.27× 确定性加速、BRAM 130/140、Fmax 140 MHz |
| 功能正确性与设计完整性 | 20 | 板上 1272/1611、逐类计数、PC/板端对比 |
| 大模型协作与技能包 | 15 | `skill/` 4 项 + `llm_collaboration_record.docx` |
| 文档质量与可复现性 | 15 | 18 页技术文档、build/board 说明、make_boot/build_app |

## 六、提交前必须处理

1. **确认实物照片**：`design_report.docx` 图 3-1 已替换为开发板实物照片，提交前再检查清晰度与图注。
2. **原始会话截图**：已导出 3 页 `llm_collaboration_record.docx`；如赛事要求原始界面，附会话截图/导出文件。
3. **开源地址**：https://github.com/zhangrunhan666-hue/bayesian_gru_zynq7020
4. **确认 SD 卡文件**：`board/BOOT.BIN` + `data/CLIPS.BIN` 必须同时存在。
5. **检查作品简介边界**：多目标 BO、稀疏变分推断未实现，报告已写成目标/后续，答辩口径要一致。
6. **HLS C 仿真**：已通过，`max_gi_err=0.000015 errors=0`，日志在 `sim/`。

## 七、当前可提交性判断

```text
工程包：基本完整（源码、报告、BOOT、CLIPS、构建输入）
技能包：完整（4 项，无 PYNQ 加分）
设计报告：18 页，优化对比/LLM/技能/复现/实物照片已补；原始界面截图可选
复现性：make_boot.ps1 + build_app.ps1 + build_steps.md 已提供
最大风险：简介中的多目标 BO/稀疏 VI 与实物不一致
```

开源地址已补；如赛事要求原始会话界面，再附截图即可。
