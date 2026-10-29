#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pure GRU (no CNN) for the prepared NVGesture 5-class clips.

Input .npz from prepare_nvgesture.py:
  x: (N, T, S, S) uint8
  y: (N,) int64
  classes: (C,) strings

Model:
  per-frame flatten S*S -> GRU(H) -> FC(C)
  dropout on x and h at every timestep (MC Dropout at inference)

Usage:
  python train_gru.py --train train.npz --test test.npz --hidden 64 --epochs 100
"""

import argparse
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset


class GRUCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.W_ih = nn.Parameter(torch.empty(3 * hidden_size, input_size))
        self.W_hh = nn.Parameter(torch.empty(3 * hidden_size, hidden_size))
        self.b_ih = nn.Parameter(torch.zeros(3 * hidden_size))
        self.b_hh = nn.Parameter(torch.zeros(3 * hidden_size))
        nn.init.xavier_uniform_(self.W_ih)
        nn.init.xavier_uniform_(self.W_hh)

    def forward(self, x, h, dropout=0.0, mc=False):
        # PyTorch gate order: r, z, n
        if dropout > 0.0 and (self.training or mc):
            x = F.dropout(x, p=dropout, training=True)
            h = F.dropout(h, p=dropout, training=True)

        gi = F.linear(x, self.W_ih, self.b_ih)
        gh = F.linear(h, self.W_hh, self.b_hh)
        i_r, i_z, i_n = gi.chunk(3, dim=1)
        h_r, h_z, h_n = gh.chunk(3, dim=1)

        r = torch.sigmoid(i_r + h_r)
        z = torch.sigmoid(i_z + h_z)
        n = torch.tanh(i_n + r * h_n)
        return (1.0 - z) * n + z * h


class GRUClf(nn.Module):
    def __init__(self, input_size, hidden_size, n_classes, dropout=0.2):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.n_classes = n_classes
        self.dropout = dropout
        self.cell = GRUCell(input_size, hidden_size)
        self.fc = nn.Linear(hidden_size, n_classes)

    def forward(self, x, mc=False):
        # x: (B, T, I)
        b, t, _ = x.shape
        h = x.new_zeros((b, self.hidden_size))
        for step in range(t):
            h = self.cell(x[:, step, :], h, self.dropout, mc)
        return self.fc(h)


def load_npz(path):
    d = np.load(path, allow_pickle=True)
    x = d["x"].astype(np.float32) / 255.0
    y = d["y"].astype(np.int64)
    classes = [str(c) for c in d["classes"]]
    x = x.reshape(x.shape[0], x.shape[1], -1)
    return x, y, classes


def evaluate(model, loader, device):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(x, mc=False)
            pred = logits.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.numel()
    return correct / max(total, 1)


def mc_predict(model, loader, k, device):
    model.eval()
    probs, labels = [], []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            ps = []
            for _ in range(k):
                logits = model(x, mc=True)
                ps.append(F.softmax(logits, dim=1))
            p = torch.stack(ps, dim=0).mean(dim=0)
            probs.append(p.cpu())
            labels.append(y)
    p = torch.cat(probs, dim=0)
    y = torch.cat(labels, dim=0)
    ent = -(p * torch.log(p + 1e-8)).sum(dim=1)
    return p, y, ent


def export_weights(model, prefix, classes):
    sd = model.state_dict()
    arrays = {
        "W_ih": sd["cell.W_ih"].detach().cpu().numpy(),
        "W_hh": sd["cell.W_hh"].detach().cpu().numpy(),
        "b_ih": sd["cell.b_ih"].detach().cpu().numpy(),
        "b_hh": sd["cell.b_hh"].detach().cpu().numpy(),
        "W_fc": sd["fc.weight"].detach().cpu().numpy(),
        "b_fc": sd["fc.bias"].detach().cpu().numpy(),
    }

    q = {}
    scales = {}
    for key, arr in arrays.items():
        scale = max(float(np.abs(arr).max()), 1e-8) / 32767.0
        q[key] = np.clip(np.round(arr / scale), -32768, 32767).astype(np.int16)
        scales[key] = np.array(scale, dtype=np.float32)

    meta = {
        "input_size": np.array(model.input_size),
        "hidden_size": np.array(model.hidden_size),
        "n_classes": np.array(model.n_classes),
        "classes": np.array(classes),
    }

    np.savez(prefix + ".npz", **q, **{k + "_scale": v for k, v in scales.items()}, **meta)

    order = ["W_ih", "W_hh", "b_ih", "b_hh", "W_fc", "b_fc"]
    with open(prefix + ".bin", "wb") as f:
        for key in order:
            f.write(q[key].tobytes(order="C"))

    print("exported", prefix + ".npz", prefix + ".bin")
    for key in order:
        print("  %-6s shape=%-16s scale=%.8f" % (key, str(q[key].shape), float(scales[key])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--test", default=None)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--dropout", type=float, default=0.2)
    ap.add_argument("--mc", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="weights")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device:", device)

    x, y, classes = load_npz(args.train)
    print("train:", x.shape, "classes:", classes)

    if args.test:
        xt, yt, classes_t = load_npz(args.test)
        print("test :", xt.shape, "classes:", classes_t)
    else:
        idx = np.random.permutation(len(x))
        split = int(len(x) * 0.8)
        xt, yt = x[idx[split:]], y[idx[split:]]
        x, y = x[idx[:split]], y[idx[:split]]
        print("no --test, split 80/20:", x.shape, xt.shape)

    train_ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    test_ds = TensorDataset(torch.from_numpy(xt), torch.from_numpy(yt))
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    model = GRUClf(x.shape[-1], args.hidden, len(classes), args.dropout).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()

    best = 0.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb, mc=False)
            loss = loss_fn(logits, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total_loss += loss.item() * yb.numel()

        acc = evaluate(model, test_loader, device)
        best = max(best, acc)
        if epoch % 5 == 0 or epoch == 1:
            print("epoch %3d  loss %.4f  test_acc %.4f" % (epoch, total_loss / len(train_ds), acc))

    print("best test acc: %.4f" % best)
    p, yt_true, ent = mc_predict(model, test_loader, args.mc, device)
    pred = p.argmax(dim=1)
    print("MC K=%d acc: %.4f  mean_entropy: %.4f" % (args.mc, (pred == yt_true).float().mean().item(), ent.mean().item()))

    export_weights(model, args.out, classes)


if __name__ == "__main__":
    main()
