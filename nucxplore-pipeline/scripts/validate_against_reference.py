#!/usr/bin/env python3
"""
Validate pipeline output against a Docker-generated reference.

Usage:
  python validate_against_reference.py \
    --new-features /path/to/new/features \
    --new-predictions /path/to/new/predictions \
    --ref-features /path/to/reference/features \
    --ref-predictions /path/to/reference/predictions

Exact equality for non-CCSM features.
Tolerance-based equality for pre/post_norm_ccsm_* features (rtol=1e-12, atol=1e-12).
Exact label equality for same-build comparisons.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def load_csvs(root: Path) -> pd.DataFrame:
    frames = []
    for p in sorted(root.glob("*.csv")):
        df = pd.read_csv(p)
        tile_key = re.sub(r"^GTEX-1F75B-0126_tile_", "", p.stem)
        df["merge_key"] = tile_key + "_" + df["nucleus_id"].astype(str)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def ccsm_cols(all_cols: list[str]) -> list[str]:
    return [c for c in all_cols if "ccsm" in c]


def non_ccsm_cols(all_cols: list[str]) -> list[str]:
    return [c for c in all_cols if "ccsm" not in c]


SKIP = {
    "nucleus_id", "tile_key", "merge_key",
    "nucleus_type", "Predicted_Label", "Confidence_Score",
    "Tissue", "Sex", "Age Bracket", "Hardy Scale", "Pathology Categories",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate against Docker-generated reference")
    parser.add_argument("--new-features", type=Path, required=True)
    parser.add_argument("--new-predictions", type=Path, required=True)
    parser.add_argument("--ref-features", type=Path, required=True)
    parser.add_argument("--ref-predictions", type=Path, required=True)
    parser.add_argument("--ccsm-rtol", type=float, default=1e-12)
    parser.add_argument("--ccsm-atol", type=float, default=1e-12)
    args = parser.parse_args()

    new_feat = load_csvs(args.new_features)
    new_pred = load_csvs(args.new_predictions)
    ref_feat = load_csvs(args.ref_features)
    ref_pred = load_csvs(args.ref_predictions)

    n_new = len(new_pred)
    n_ref = len(ref_pred)
    print(f"New pipeline: {n_new} nuclei")
    print(f"Reference:    {n_ref} nuclei")

    matched = new_pred.merge(ref_pred, on="merge_key", suffixes=("_new", "_ref"))
    print(f"Matched:      {len(matched)} nuclei")

    if len(matched) < n_new or len(matched) < n_ref:
        print(f"  Missing: {n_new - len(matched)} new-only, {n_ref - len(matched)} ref-only")

    # Label comparison
    agree = (matched["Predicted_Label_new"].astype(str) == matched["Predicted_Label_ref"].astype(str)).mean()
    print(f"\nPredicted_Label exact agreement: {agree:.6%} ({int(agree * len(matched))}/{len(matched)})")

    cs_new = pd.to_numeric(matched["Confidence_Score_new"], errors="coerce")
    cs_ref = pd.to_numeric(matched["Confidence_Score_ref"], errors="coerce")
    cs_corr = cs_new.corr(cs_ref)
    print(f"Confidence_Score correlation: {cs_corr:.10f}")

    # Feature comparison
    mf = new_feat.merge(ref_feat, on="merge_key", suffixes=("_new", "_ref"))
    common = sorted((set(new_feat.columns) & set(ref_feat.columns)) - SKIP)
    ccsms = ccsm_cols(common)
    others = non_ccsm_cols(common)

    print(f"\n--- Non-CCSM features ({len(others)} columns) ---")
    non_ccsm_pass = True
    for col in others:
        v1 = pd.to_numeric(mf[f"{col}_new"], errors="coerce")
        v2 = pd.to_numeric(mf[f"{col}_ref"], errors="coerce")
        if not (v1 == v2).all():
            diff = (v1 != v2).sum()
            print(f"  FAIL: {col} — {diff} nuclei differ (expected exact match)")
            non_ccsm_pass = False
    if non_ccsm_pass:
        print("  ALL pass (exact match)")

    print(f"\n--- CCSM features ({len(ccsms)} columns) ---")
    ccsm_pass = True
    for col in ccsms:
        v1 = pd.to_numeric(mf[f"{col}_new"], errors="coerce")
        v2 = pd.to_numeric(mf[f"{col}_ref"], errors="coerce")
        mask = v1.notna() & v2.notna()
        if not mask.any():
            continue
        max_rel = np.abs(v1[mask] - v2[mask]).max()
        within = np.allclose(v1[mask], v2[mask], rtol=args.ccsm_rtol, atol=args.ccsm_atol)
        if not within:
            n_diff = (~np.isclose(v1[mask], v2[mask], rtol=args.ccsm_rtol, atol=args.ccsm_atol)).sum()
            print(f"  FAIL: {col} — {n_diff} nuclei exceed tolerance (max diff={max_rel:.2e})")
            ccsm_pass = False
    if ccsm_pass:
        print(f"  ALL pass (rtol={args.ccsm_rtol}, atol={args.ccsm_atol})")

    if not non_ccsm_pass or not ccsm_pass:
        print("\nVALIDATION FAILED")
        return 1

    print("\nVALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
