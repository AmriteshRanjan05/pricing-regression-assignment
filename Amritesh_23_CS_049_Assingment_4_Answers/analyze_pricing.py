#!/usr/bin/env python3
"""Analyze Pricing Refactor Regression assignment.

Uses only Python's standard library so the investigation is easy to reproduce.
"""

import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

CSV_PATH = Path(__file__).with_name("pricing_diff.csv")


def read_rows(path):
    rows = []
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "order_id": int(r["order_id"]),
                    "weight_kg": Decimal(r["weight_kg"]),
                    "distance_km": Decimal(r["distance_km"]),
                    "category": r["category"],
                    "express": r["express"].strip().lower() == "true",
                    "coupon": r["coupon"] or "",
                    "v1_total": Decimal(r["v1_total"]),
                    "v2_total": Decimal(r["v2_total"]),
                }
            )
    return rows


def main():
    rows = read_rows(CSV_PATH)

    def delta(r):
        return r["v2_total"] - r["v1_total"]

    def abs_delta(r):
        return abs(delta(r))

    # Q1: literal comparison, before accounting for expected differences.
    naive_nonzero = [r for r in rows if r["v2_total"] != r["v1_total"]]

    # Genuine regression identified from the data: fragile + express.
    affected = [
        r for r in rows
        if r["category"] == "fragile" and r["express"]
    ]

    # Sanity-check that every meaningful non-books difference is exactly in
    # the affected group. A 2-cent threshold cleanly separates the baseline
    # noise (<= 0.02) from the regression in this dataset.
    nonbooks_meaningful = [
        r for r in rows
        if r["category"] != "books" and abs_delta(r) > Decimal("0.02")
    ]
    unexpected_meaningful = [
        r for r in nonbooks_meaningful
        if not (r["category"] == "fragile" and r["express"])
    ]

    # Q3: v2 - v1 is positive for the affected rows, so this is the total
    # amount overcharged by the new implementation.
    total_overcharge = sum((delta(r) for r in affected), Decimal("0"))

    # Q4: JSON key in the assignment specifies mean absolute difference.
    baseline = [
        r for r in rows
        if r["category"] != "books"
        and not (r["category"] == "fragile" and r["express"])
    ]
    baseline_mean_abs = (
        sum((abs_delta(r) for r in baseline), Decimal("0"))
        / Decimal(len(baseline))
    )

    baseline_max_abs = max(abs_delta(r) for r in baseline)
    affected_min = min(delta(r) for r in affected)
    affected_max = max(delta(r) for r in affected)

    category_express = defaultdict(list)
    for r in rows:
        category_express[(r["category"], r["express"])].append(delta(r))

    print(f"Rows: {len(rows)}")
    print(f"Q1 naive non-zero count: {len(naive_nonzero)}")
    print(f"Q2 affected count: {len(affected)}")
    print("Q2 condition: category='fragile' AND express=True")
    print(f"Q3 total overcharge: ${total_overcharge}")
    print(f"Q4 baseline mean absolute difference: {baseline_mean_abs}")
    print(f"Q4 baseline max absolute difference: ${baseline_max_abs}")
    print(f"Affected delta range: ${affected_min} to ${affected_max}")
    print(f"Non-books differences > $0.02: {len(nonbooks_meaningful)}")
    print(f"Unexpected non-books differences outside affected group: {len(unexpected_meaningful)}")

    print("\nCategory x express mean absolute difference:")
    for key in sorted(category_express):
        vals = category_express[key]
        mean_abs = sum(abs(v) for v in vals) / Decimal(len(vals))
        print(f"  {key}: n={len(vals)}, mean_abs=${mean_abs}")

    answers = {
        "q1_naive_nonzero_count": len(naive_nonzero),
        "q2_affected_count": len(affected),
        "q2_affected_category": "fragile (express=True)",
        "q3_total_overcharge": float(total_overcharge),
        "q4_baseline_mean_abs_diff": float(baseline_mean_abs),
    }
    print("\nJSON:")
    print(json.dumps(answers, indent=2))

    assert len(unexpected_meaningful) == 0
    assert all(delta(r) > Decimal("0.02") for r in affected)


if __name__ == "__main__":
    main()
