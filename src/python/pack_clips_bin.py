#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pack a Jester validation .npz into CLIPS.BIN for the SD-card reader."""

import argparse
import struct
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--npz", required=True, help="jester3_val_full.npz")
ap.add_argument("--out", default="CLIPS.BIN")
args = ap.parse_args()

d = np.load(args.npz)
x = d["x"].astype(np.uint8)
y = d["y"].astype(np.uint8)
n, t, s, _ = x.shape

with open(args.out, "wb") as f:
    f.write(b"JCLP")
    f.write(struct.pack("<III", n, t, s))
    f.write(y.tobytes())
    f.write(x.tobytes())

print(args.out, "clips", n, "T", t, "S", s,
      "labels", np.bincount(y).tolist())
