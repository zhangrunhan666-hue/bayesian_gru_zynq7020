#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quantized (int16) GRU inference check, matching the exported weights.

Loads:
  test.npz       x: (N,T,S,S) uint8, y: (N,), classes
  weights.npz    int16 W_ih/W_hh/b_ih/b_hh/W_fc/b_fc + per-tensor scales

Runs the same GRU equations as the hardware:
  r,z,n = sigmoid/tanh(...)
  h' = (1-z)*n + z*h
  logits = W_fc h + b_fc

Optional MC Dropout:
  --mc 5 --dropout 0.15

Usage:
  python predict_quant.py --test test.npz --weights weights.npz
  python predict_quant.py --test test.npz --weights weights.npz --mc 5 --dropout 0.15
"""

import argparse
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def softmax(x):
    x = x - x.max(axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)


def load_weights(path):
    d = np.load(path, allow_pickle=True)
    w = {}
    for k in ["W_ih", "W_hh", "b_ih", "b_hh", "W_fc", "b_fc"]:
        w[k] = d[k].astype(np.float32) * float(d[k + "_scale"])
    w["classes"] = [str(c) for c in d["classes"]]
    w["input_size"] = int(d["input_size"])
    w["hidden_size"] = int(d["hidden_size"])
    w["n_classes"] = int(d["n_classes"])
    return w


def forward_one(x, w, hidden, dropout=0.0, rng=None):
    # x: (T, I), already float [0,1]
    T, I = x.shape
    h = np.zeros(hidden, dtype=np.float32)
    H = hidden

    for t in range(T):
        xt = x[t]
        if dropout > 0.0 and rng is not None:
            xt = xt * (rng.random(I) >= dropout)
            h = h * (rng.random(H) >= dropout)

        gi = w["W_ih"] @ xt + w["b_ih"]
        gh = w["W_hh"] @ h + w["b_hh"]

        r = sigmoid(gi[:H] + gh[:H])
        z = sigmoid(gi[H:2 * H] + gh[H:2 * H])
        n = np.tanh(gi[2 * H:] + r * gh[2 * H:])
        h = (1.0 - z) * n + z * h

    return w["W_fc"] @ h + w["b_fc"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--mc", type=int, default=0, help="0 = deterministic; 5 = MC Dropout")
    ap.add_argument("--dropout", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=123)
    args = ap.parse_args()

    d = np.load(args.test, allow_pickle=True)
    x = d["x"].astype(np.float32) / 255.0
    y = d["y"].astype(np.int64)
    classes = [str(c) for c in d["classes"]]
    x = x.reshape(x.shape[0], x.shape[1], -1)

    w = load_weights(args.weights)
    hidden = w["hidden_size"]
    n_classes = w["n_classes"]
    print("test", x.shape, "classes", classes)
    print("hidden", hidden, "n_classes", n_classes)

    rng = np.random.default_rng(args.seed)
    probs = []
    for i in range(len(x)):
        if args.mc and args.mc > 0:
            ps = []
            for _ in range(args.mc):
                logits = forward_one(x[i], w, hidden, args.dropout, rng)
                ps.append(softmax(logits[None, :])[0])
            probs.append(np.mean(ps, axis=0))
        else:
            logits = forward_one(x[i], w, hidden, 0.0, None)
            probs.append(softmax(logits[None, :])[0])

    probs = np.stack(probs, axis=0)
    pred = probs.argmax(axis=1)
    acc = float((pred == y).mean())
    ent = -(probs * np.log(probs + 1e-8)).sum(axis=1)

    print("accuracy: %.4f" % acc)
    print("mean entropy: %.4f" % ent.mean())
    for c in range(n_classes):
        m = y == c
        if m.any():
            print("  %-12s n=%3d acc=%.3f ent=%.3f" % (classes[c], m.sum(), (pred[m] == y[m]).mean(), ent[m].mean()))

    # simple rejection / risk-coverage curve
    print("\nthreshold  coverage  accuracy_on_accept  reject_rate")
    for th in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        keep = ent <= th
        cov = keep.mean()
        acc_keep = (pred[keep] == y[keep]).mean() if keep.any() else 0.0
        print("  %.1f       %.3f     %.3f               %.3f" % (th, cov, acc_keep, 1 - cov))


if __name__ == "__main__":
    main()
