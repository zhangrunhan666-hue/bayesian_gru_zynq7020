# PC 训练与量化链路

本目录用于从 Jester 原始数据复现模型权重。训练和量化在 PC 上完成，板端只运行导出的 C 头文件。

## 依赖

```text
Python 3.10+
numpy
torch
opencv-python
```

安装示例：

```powershell
pip install numpy torch opencv-python
```

## 1. 数据准备

需要 Jester 官方：

```text
20bn-jester-v1/<video_id>/*.jpg
jester_labels/train.csv
jester_labels/validation.csv
```

三类、每类 2,000 段示例：

```powershell
python prepare_jester.py `
  --root D:\datasets\Jester `
  --train-csv D:\datasets\Jester\jester_labels\train.csv `
  --val-csv D:\datasets\Jester\jester_labels\validation.csv `
  --classes "Stop Sign" "Thumb Up" "Thumb Down" `
  --size 32 --n-frames 8 --crop-size 64 --diff `
  --max-per-class 2000 `
  --out-train jester3_train_2k.npz `
  --out-val jester3_val_1611.npz
```

全量 3 类训练集用 `--max-per-class 0`。

## 2. 训练

```powershell
python train_gru.py `
  --train jester3_train_2k.npz `
  --test jester3_val_1611.npz `
  --hidden 64 --epochs 100 --lr 0.0005 --dropout 0.15 --mc 5 `
  --out weights_jester3_2k
```

本作品最终使用的是全量 13,100 段训练集：

```text
weights_jester3_full.npz / .bin
```

## 3. 量化评估

```powershell
python predict_quant.py `
  --test jester3_val_full.npz `
  --weights weights_jester3_full.npz
```

期望约 79.76%（1285/1611）。

## 4. 导出 C / HLS 头文件

`gen_jester_headers_full.py` 中的路径是作者环境的绝对路径，复现时请改成你的工作目录。它会生成：

```text
src/vitis/weights.h
src/vitis/clips.h（旧嵌入式方案，可选）
src/hls/weights_hls.h
```

## 5. 打包 CLIPS.BIN

```powershell
python pack_clips_bin.py `
  --npz jester3_val_full.npz `
  --out ..\..\data\CLIPS.BIN
```

格式见 `data/README.md`。

## 说明

- Jester 原始数据体积大，不随仓库提交；请从官方下载。
- 训练/量化脚本仅依赖 numpy、torch、opencv。
- 板端使用 `src/vitis/gru_ip.c` 与 `src/hls/gru_mv.cpp`。
