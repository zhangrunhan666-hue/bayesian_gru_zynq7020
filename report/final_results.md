# Jester 3 类 GRU 硬件加速最终结果

日期：2026-10-29  
参赛数据集：Jester（3 类 + 帧差）

## 平台

- 开发板：博宸 ZYNQ MINI 7020，XC7Z020-2CLG400I
- PS：Cortex-A9，667 MHz
- PL：FCLK0 50 MHz
- 模型：纯 GRU，H=64，T=8，输入 32×32 灰度，int16 量化
- PL：计算 `gi = W_ih * x + b_ih`
- PS：MC Dropout、`W_hh`、门控、FC、entropy/拒识

## 数据集

- 训练：Jester 官方 train 中 3 类全部样本，13,100 段
  - Stop Sign   4,337
  - Thumb Up    4,373
  - Thumb Down  4,390
- 验证/上板：Jester 官方 validation 中 3 类全部样本，1,611 段
  - Stop Sign     536
  - Thumb Up      539
  - Thumb Down    536
- 预处理：64×64 中心裁剪 → 32×32，帧差
- 未使用官方 test

## 准确率

```text
训练 13,100 段的浮点最佳：80.70%
PC int16 量化：            1285/1611 = 79.76%
PC MC K=5：                79.39%
板上 MC K=5：              1272/1611 = 78.96%

Stop Sign:   380/536  = 70.9%
Thumb Up:    424/539  = 78.7%
Thumb Down:  468/536  = 87.3%
```

板上与 PC 量化误差约 **0.8 个百分点**，属于 MC 随机采样和定点误差范围。

## 自适应 MC Dropout 不确定性（板上）

```text
Kmin=3，Kmax=5，early entropy<0.30，p=0.15

accept H<=0.50：1042/1201 = 86.8%
reject H>0.50 ： 230/410  = 56.1%

mean entropy correct = 0.184
mean entropy wrong   = 0.467
max entropy：clip 1434，H=1.094

自适应 K 分布：
  K=3：1061 段（65.9%）
  K=4：   19 段
  K=5：  531 段（33.0%）

覆盖：1201/1611 = 74.6%
拒识： 410/1611 = 25.4%
```

结论：

- 接受样本准确率 **86.8%**，比总体 78.96% 高约 **7.8 个百分点**；
- 拒识样本准确率只有 **56.1%**；
- 错误样本平均 entropy 是正确样本的 **约 2.5 倍**；
- 2/3 样本只跑 K=3，动态采样有效。

### 固定 K=5 对比

```text
固定 K=5：1272/1611，69,085 ms，42 ms/clip
自适应  ：1272/1611，51,047 ms，31 ms/clip
```

准确率不变，时间降低约 **26%**。

## 部署方式

为控制 BOOT 体积，验证集不编译进 ELF：

```text
SD 卡根目录：
  BOOT.BIN     4,284,876 字节
  CLIPS.BIN   13,198,939 字节

应用启动后：
  FatFs 挂载 SD
  读取 CLIPS.BIN 头/标签
  逐段读 8×1024 字节到 DDR 缓冲
  送入 GRU
```

这样 BOOT 只有约 4.3 MB，可正常 SD 启动。

## 性能

```text
板上自适应 K=3/5：51,047 ms，31 ms/clip
1,611 段 / 51.0 秒
```

确定性版本的硬件加速比（1,200 段架构，同 -O2）：

```text
PS-only：32,467 ms，27 ms/clip
PS+PL ： 9,925 ms， 8 ms/clip
纯硬件加速比：3.27×
```

## 资源

```text
BRAM: 130 / 140  (92.86%)
DSP:   24 / 220
LUT:   2032
FF:    2159
HLS Fmax: 140.06 MHz
```

## 结论

- 使用 Jester 3 类全部 13,100 段训练，1,611 段完整验证；
- 板上自适应 K=3/5 准确率 78.96%，接受子集 86.8%；
- BOOT 4.3 MB，验证集通过 SD `CLIPS.BIN` 读取；
- 贝叶斯部分为 MC Dropout 近似推理，采样/集成在 PS，PL 加速主干 `W_ih`；
- 动态推理为基于 entropy 的自适应 K 采样，约 2/3 样本只跑 K=3。

## 文件

```text
Jester 全量训练权重：D:\dsh-projects\jester_gru\weights_jester3_full.npz
CLIPS.BIN：D:\dsh-projects\jester_gru\CLIPS.BIN
BOOT：D:\dsh-projects\kth_fpga\BOOT_jester_sd_adaptive.bin
XSA：D:\dsh-projects\kth_fpga\ps7020_gru_jester.xsa
应用 ELF：D:\dsh-projects\kth_fpga\vitis_ws\hello_uart\build\hello_uart_jester_sd_adaptive.elf
```
