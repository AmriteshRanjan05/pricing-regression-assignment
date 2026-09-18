# Pricing Refactor Regression

## Q1. Naive non-zero count

There are **16,000 rows** where `v2_total != v1_total`.

This is not the number of orders affected by a real bug because the assignment says two other sources of difference are expected: the `books` category was intentionally repriced, and the refactor can introduce tiny floating-point/rounding differences of a cent or two. A raw inequality therefore mixes expected changes and noise with the actual regression.

## Q2. Genuine pricing regression

The exact number of genuinely affected orders is **985**.

The affected orders all share:

- `category = fragile`
- `express = True`

The key evidence is that, after removing `books`, every other category/express group has differences no larger than **$0.02**, while all 985 `fragile + express` orders have a positive difference greater than **$0.02**. Their `v2_total - v1_total` differences range from **$5.08 to $34.98**.

So this is a distinct systematic pattern, not general floating-point drift.

## Q3. Total amount overcharged

For the 985 affected orders, calculate `v2_total - v1_total` and sum the results.

**Total overcharge = $19,779.14**

Every affected difference is positive, so the new implementation consistently charges more than the old implementation for this group.

## Q4. Baseline sanity check

For orders that are **not affected by the bug and are not in the `books` category**, the mean absolute difference is:

**$0.009882653061224489795918367347**

The maximum absolute difference in this baseline group is only **$0.02**.

That gives a strong separation from the regression group, whose smallest difference is **$5.08**. The affected orders are therefore not just another example of the normal one- or two-cent numerical noise described in the assignment.

## Q5. Bonus: likely code-level bug

The source code is not provided, so this is a data-based hypothesis rather than a confirmed implementation detail.

The pattern is consistent with the **express surcharge being applied twice in the `fragile + express` path** of the refactored pricing code. For the 772 affected orders without a coupon, the extra amount is approximately:

`5 + 0.10 * distance_km`

For the 213 `SAVE10` orders, the extra amount is approximately 90% of that expression. The mean absolute residuals against those simple formulas are only about one cent, which matches the expected rounding noise. The affected difference also has a very strong positive correlation with distance (`r ≈ 0.994562`).

In plain English: the refactor appears to be adding an express distance-based adjustment a second time for fragile orders.

## Investigation process

- Loaded the CSV and checked the row count, columns, categories, and boolean `express` values.
- First tried the most obvious check: count every row where `v2_total != v1_total`. This produced **16,000**, but that result was immediately treated as a dead end because the assignment says some differences are expected.
- Calculated `v2_total - v1_total` for every order and examined the size of the differences rather than only whether they were non-zero.
- Excluded the documented `books` category from regression detection because its pricing change is intentional.
- Grouped the remaining rows by `category` and `express` to look for a systematic subgroup.
- Found one unique non-books group whose every row was outside the cent-level noise band: `fragile + express`, with **985** orders.
- Verified that there were **zero** other non-books rows with an absolute difference above **$0.02**.
- Summed the affected differences to get the total customer overcharge and calculated the unaffected non-books baseline mean absolute difference for Q4.
- As a Q5 diagnostic, checked whether the affected difference follows a distance-based express charge; the observed values closely match `5 + 0.10 * distance_km` (or 90% of it for `SAVE10` orders).

## Reproducibility

Run the script from the directory containing both files:

```bash
python3 analyze_pricing.py
```

The script uses only Python's standard library. It first discovers the suspicious category/express group from the data, rather than starting with `fragile + express` as an assumption, and then validates the final numbers with assertions.
