#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jester (20BN-Jester) -> 8-class clip dataset for a pure GRU.

Expected layout after extracting the official Jester tars:

  D:\\datasets\\Jester\\
    20bn-jester-v1\\
      10001\\00001.jpg ... 00030.jpg
      10002\\...
    jester-v1-train.csv
    jester-v1-validation.csv
    jester-v1-labels.csv

CSV format is normally: video_id;label  (Jester uses semicolon).

Usage (8 classes, 32x32, 8 frames):
  python prepare_jester.py --root D:\\datasets\\Jester ^
    --train-csv D:\\datasets\\Jester\\jester_labels\\train.csv ^
    --val-csv D:\\datasets\\Jester\\jester_labels\\validation.csv ^
    --classes "Stop Sign" "Thumb Up" "Thumb Down" "Swiping Left" "Swiping Right" "Swiping Down" "Swiping Up" "Pulling Two Fingers In" ^
    --size 32 --n-frames 8 --max-per-class 400 ^
    --out-train jester_train.npz --out-val jester_val.npz
"""

import argparse
import csv
import glob
import os
import sys
from collections import Counter

import cv2
import numpy as np


def read_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        first = f.readline()
        delimiter = ";" if ";" in first else ","
        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if len(row) < 2:
                continue
            vid = row[0].strip()
            label = row[1].strip()
            if vid.lower() in ("video_id", "id", "video"):
                continue
            rows.append((vid, label))
    return rows


def read_labels(path):
    """Optional: label_id -> label name."""
    mapping = {}
    if not path or not os.path.isfile(path):
        return mapping
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                mapping[row[0].strip()] = row[1].strip()
            elif len(row) == 1:
                mapping[row[0].strip()] = row[0].strip()
    return mapping


def find_video_dir(root, vid):
    # Jester layout is fixed: <root>/20bn-jester-v1/<video_id>.
    # Avoid recursive glob: with 148k dirs it makes missing IDs extremely slow.
    for base in (os.path.join(root, "20bn-jester-v1"), root):
        p = os.path.join(base, vid)
        if os.path.isdir(p):
            return p
    return None


def read_clip(vdir, n_frames, size, crop, use_diff, crop_size=0):
    files = sorted(glob.glob(os.path.join(vdir, "*.jpg")) +
                   glob.glob(os.path.join(vdir, "*.jpeg")) +
                   glob.glob(os.path.join(vdir, "*.png")))
    if len(files) < n_frames:
        return None

    idx = np.linspace(0, len(files) - 1, n_frames).astype(int)
    grays = []
    for i in idx:
        img = cv2.imread(files[i], cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        if crop:
            h, w = img.shape[:2]
            s = min(h, w)
            y0 = (h - s) // 2
            x0 = (w - s) // 2
            img = img[y0:y0 + s, x0:x0 + s]
            if crop_size and crop_size < s:
                y0 = (s - crop_size) // 2
                x0 = (s - crop_size) // 2
                img = img[y0:y0 + crop_size, x0:x0 + crop_size]
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
        grays.append(img)

    if use_diff:
        diffs = []
        prev = None
        for g in grays:
            if prev is None:
                diffs.append(np.zeros_like(g))
            else:
                diffs.append(cv2.absdiff(g, prev))
            prev = g
        grays = diffs

    return np.stack(grays, axis=0).astype(np.uint8)


def build(rows, root, classes, label_map, args, split_name):
    xs, ys = [], []
    counts = Counter()
    bad = 0
    for vid, raw_label in rows:
        label = label_map.get(raw_label, raw_label)
        if label not in classes:
            continue
        if args.max_per_class and counts[label] >= args.max_per_class:
            continue
        vdir = find_video_dir(root, vid)
        if vdir is None:
            bad += 1
            if bad <= 10:
                print("MISS", split_name, vid)
            continue
        clip = read_clip(vdir, args.n_frames, args.size, not args.no_crop, args.diff, args.crop_size)
        if clip is None:
            bad += 1
            continue
        xs.append(clip)
        ys.append(classes.index(label))
        counts[label] += 1
        if len(xs) % 100 == 0:
            print("loaded", split_name, len(xs))

    if not xs:
        print("empty", split_name)
        return None, None, counts, bad
    return np.stack(xs), np.array(ys, dtype=np.int64), counts, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Jester root containing 20bn-jester-v1")
    ap.add_argument("--train-csv", required=True)
    ap.add_argument("--val-csv", required=True)
    ap.add_argument("--labels-csv", default=None)
    ap.add_argument("--classes", nargs="+", required=True)
    ap.add_argument("--size", type=int, default=32)
    ap.add_argument("--n-frames", type=int, default=8)
    ap.add_argument("--max-per-class", type=int, default=0)
    ap.add_argument("--diff", action="store_true")
    ap.add_argument("--crop-size", type=int, default=0,
                    help="center crop size before resizing (0 = full square)")
    ap.add_argument("--no-crop", action="store_true")
    ap.add_argument("--out-train", default="jester_train.npz")
    ap.add_argument("--out-val", default="jester_val.npz")
    args = ap.parse_args()

    label_map = read_labels(args.labels_csv) if args.labels_csv else {}
    train_rows = read_csv(args.train_csv)
    val_rows = read_csv(args.val_csv)
    print("train csv", len(train_rows), "val csv", len(val_rows), "classes", args.classes)

    xtr, ytr, ctr, btr = build(train_rows, args.root, args.classes, label_map, args, "train")
    xva, yva, cva, bva = build(val_rows, args.root, args.classes, label_map, args, "val")
    if xtr is None or xva is None:
        print("no data; check --root and class names")
        sys.exit(1)

    np.savez_compressed(args.out_train, x=xtr, y=ytr, classes=np.array(args.classes))
    np.savez_compressed(args.out_val, x=xva, y=yva, classes=np.array(args.classes))

    print("saved", args.out_train, xtr.shape)
    print("saved", args.out_val, xva.shape)
    print("bad train/val", btr, bva)
    for c in args.classes:
        print("  %-12s train=%d val=%d" % (c, ctr[c], cva[c]))


if __name__ == "__main__":
    main()
