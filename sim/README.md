# 仿真与验证

## 当前状态

- HLS C testbench 已更新为 **Jester 全量权重 + 第 1 帧非零输入**，参考 `TB_GI` 为 HLS 未经 /255 的原始输出。
- **C 仿真已通过**：`max_gi_err=0.000015, errors=0`，日志见 `gru_mv_csim.log` / `hls_run_csim.log`。
- 功能正确性同时以 **板端实测 + PC int16 量化对比** 为依据。

## 板端/PC 对比

| 项目 | PC int16 | 板端 |
|---|---|---|
| 总体 | 1285/1611 = 79.76% | 1272/1611 = 78.96%（自适应 K） |
| Stop Sign | 397/536 | 389/536 |
| Thumb Up | 419/539 | 417/539 |
| Thumb Down | 469/536 | 466/536 |

差异来自 MC Dropout 随机采样；确定性版本与 PC 量化一致。

## 复现 C 仿真

1. 打开 Vitis HLS / Vitis 2026.1；
2. 新建 HLS 工程，top=`gru_mv`，part=`xc7z020clg400-2`；
3. 加入 `src/hls/gru_mv.cpp`、`gru_mv.h`、`weights_hls.h`、`gru_mv_tb.cpp`、`tb_data.h`；
4. 执行 C SIMULATION，期望 `errors=0`。
