#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate C/HLS headers for the Jester 3-class frame-difference GRU."""

import os
import numpy as np

ROOT = r"D:\dsh-projects\jester_gru"
OUT_SRC = r"D:\dsh-projects\kth_fpga\vitis_ws\hello_uart\src"
OUT_HLS = r"D:\dsh-projects\kth_fpga\hls_gru"

w = np.load(os.path.join(ROOT, "weights_jester3_full.npz"), allow_pickle=True)
t = np.load(os.path.join(ROOT, "jester3_val_full.npz"), allow_pickle=True)

classes = [str(c) for c in w["classes"]]
I = int(w["input_size"])
H = int(w["hidden_size"])
C = int(w["n_classes"])
T = int(t["x"].shape[1])
S = int(t["x"].shape[2])
keys = ["W_ih", "W_hh", "b_ih", "b_hh", "W_fc", "b_fc"]
arrays = {k: w[k].astype(np.int16) for k in keys}
scales = {k: float(w[k + "_scale"]) for k in keys}

assert (I, H, C, T, S) == (1024, 64, 3, 8, 32), (I, H, C, T, S)
assert classes == ["Stop Sign", "Thumb Up", "Thumb Down"], classes


def fmt_int16(name, arr, per_line=16):
    flat = arr.reshape(-1)
    lines = [f"static const int16_t {name}[{flat.size}] = {{"]
    for i in range(0, flat.size, per_line):
        chunk = flat[i:i + per_line]
        lines.append("    " + ", ".join(str(int(v)) for v in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)


def fmt_i16_2d(name, arr, per_line=16):
    rows, cols = arr.shape
    lines = [f"static const short {name}[{rows}][{cols}] = {{"]
    for r in range(rows):
        lines.append("  {")
        for i in range(0, cols, per_line):
            chunk = arr[r, i:i + per_line]
            lines.append("    " + ", ".join(str(int(v)) for v in chunk) + ",")
        lines.append("  },")
    lines.append("};")
    return "\n".join(lines)


def fmt_i16_1d(name, arr, per_line=16):
    flat = arr.reshape(-1)
    lines = [f"static const short {name}[{flat.size}] = {{"]
    for i in range(0, flat.size, per_line):
        chunk = flat[i:i + per_line]
        lines.append("    " + ", ".join(str(int(v)) for v in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)


def fmt_scalar(name, val):
    return f"static const float {name} = {val:.12e}f;"


# app weights.h
lines = []
lines += ["#ifndef GRU_WEIGHTS_H", "#define GRU_WEIGHTS_H", "#include <stdint.h>", ""]
lines += [f"#define GRU_INPUT  {I}", f"#define GRU_HIDDEN {H}",
          f"#define GRU_CLASSES {C}", f"#define GRU_T {T}", f"#define GRU_S {S}", ""]
lines += ["static const char *GRU_CLASS_NAMES[GRU_CLASSES] = {"]
lines += [f'    "{c}",' for c in classes]
lines += ["};", ""]
for k in keys:
    lines += [fmt_int16(k, arrays[k]), ""]
for k in keys:
    lines += [fmt_scalar(k + "_scale", scales[k])]
lines += ["", "#endif"]
open(os.path.join(OUT_SRC, "weights.h"), "w", encoding="utf-8").write("\n".join(lines))

# HLS weights_hls.h (kernel only needs W_ih, b_ih)
hls = []
hls += ["#ifndef GRU_WEIGHTS_HLS_H", "#define GRU_WEIGHTS_HLS_H", "#include <ap_int.h>", ""]
hls += [f"#define GRU_INPUT  {I}", f"#define GRU_HIDDEN {H}",
        f"#define GRU_GATES  {3 * H}", ""]
hls += [fmt_i16_2d("W_ih", arrays["W_ih"]), ""]
hls += [fmt_i16_1d("b_ih", arrays["b_ih"]), ""]
hls += [fmt_scalar("W_ih_scale", scales["W_ih"]), fmt_scalar("b_ih_scale", scales["b_ih"]), "", "#endif"]
open(os.path.join(OUT_HLS, "weights_hls.h"), "w", encoding="utf-8").write("\n".join(hls))

# clips.h: all 1200 validation clips
x = t["x"].astype(np.uint8)
y = t["y"].astype(np.int64)
n = x.shape[0]
assert x.shape == (n, T, S, S), x.shape
clip_lines = []
clip_lines += ["#ifndef GRU_CLIPS_H", "#define GRU_CLIPS_H", "#include <stdint.h>", ""]
clip_lines += [f"#define CLIP_COUNT {n}", f"#define CLIP_T {T}", f"#define CLIP_S {S}", ""]
clip_lines += [f"static const unsigned char CLIPS[{n}][{T}][{S * S}] = {{"]
for i in range(n):
    clip_lines.append("  {")
    for j in range(T):
        vals = x[i, j].reshape(-1)
        clip_lines.append("    {" + ", ".join(str(int(v)) for v in vals) + "},")
    clip_lines.append("  },")
clip_lines += ["};", ""]
clip_lines += [f"static const unsigned char CLIP_LABEL[{n}] = {{"]
for i in range(0, n, 32):
    clip_lines.append("    " + ", ".join(str(int(v)) for v in y[i:i + 32]) + ",")
clip_lines += ["};", "", "#endif"]
open(os.path.join(OUT_SRC, "clips.h"), "w", encoding="utf-8").write("\n".join(clip_lines))

print("classes", classes)
print("I,H,C,T,S", I, H, C, T, S)
print("clips", n, "per-class", np.bincount(y, minlength=C).tolist())
print("wrote", os.path.join(OUT_SRC, "weights.h"))
print("wrote", os.path.join(OUT_HLS, "weights_hls.h"))
print("wrote", os.path.join(OUT_SRC, "clips.h"))
