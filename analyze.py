import json
from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# CONFIG & PATH RESOLUTION
# ============================================================
POSSIBLE_INPUT_PATHS = [
    Path("pricing_diff.csv"),
    Path("assignment4 (2)/pricing_diff.csv"),
    Path("assignment4 (2) (1)/assignment4 (2)/pricing_diff.csv"),
    Path("../assignment4 (2)/pricing_diff.csv"),
]

INPUT_FILE = None
for p in POSSIBLE_INPUT_PATHS:
    if p.exists():
        INPUT_FILE = p
        break

if INPUT_FILE is None:
    script_dir = Path(__file__).parent
    for p in POSSIBLE_INPUT_PATHS:
        full_p = script_dir / p
        if full_p.exists():
            INPUT_FILE = full_p
            break

if INPUT_FILE is None:
    raise FileNotFoundError("Could not locate 'pricing_diff.csv'. Please ensure it exists in the workspace.")

OUTPUT_JSON = "answers.json"

print(f"Loading data from: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)

# Compute price difference metrics
df['diff'] = df['v2_total'] - df['v1_total']
df['abs_diff'] = df['diff'].abs()

total_orders = len(df)

# ============================================================
# Q1: NAIVE NON-ZERO COUNT
# ============================================================
q1_naive_nonzero_count = int((df['v2_total'] != df['v1_total']).sum())

print("=" * 70)
print("1. NAIVE NON-ZERO COUNT")
print("=" * 70)
print(f"Total orders: {total_orders}")
print(f"Rows where v2_total != v1_total: {q1_naive_nonzero_count} ({q1_naive_nonzero_count / total_orders * 100:.1f}%)")

# ============================================================
# Q2: AFFECTED ORDERS (GENUINE PRICING REGRESSION)
# ============================================================
affected_mask = (df['category'] == 'fragile') & (df['express'] == True)
q2_affected_count = int(affected_mask.sum())
q2_affected_category = "fragile"

print("\n" + "=" * 70)
print("2. GENUINE REGRESSION IDENTIFICATION")
print("=" * 70)
print(f"Affected Order Count: {q2_affected_count}")
print(f"Affected Category: {q2_affected_category}")
print(f"Condition: category == 'fragile' AND express == True")

print("\nCategory x Express breakdown of orders with |diff| > 0.05:")
for cat in df['category'].unique():
    for exp in [True, False]:
        sub = df[(df['category'] == cat) & (df['express'] == exp)]
        large_diff_count = (sub['abs_diff'] > 0.05).sum()
        print(f"  Category: {cat:12s} | Express: {str(exp):5s} | Total: {len(sub):5d} | Large Diff (>0.05): {large_diff_count}")

# ============================================================
# Q3: TOTAL OVERCHARGE
# ============================================================
q3_total_overcharge = float(df.loc[affected_mask, 'diff'].sum())

print("\n" + "=" * 70)
print("3. TOTAL OVERCHARGE AMOUNT")
print("=" * 70)
print(f"Total Overcharge: ${q3_total_overcharge:,.2f}")
print(f"Average overcharge per affected order: ${df.loc[affected_mask, 'diff'].mean():.2f}")
print(f"Min overcharge: ${df.loc[affected_mask, 'diff'].min():.2f}")
print(f"Max overcharge: ${df.loc[affected_mask, 'diff'].max():.2f}")

# ============================================================
# Q4: BASELINE MEAN ABSOLUTE DIFFERENCE
# ============================================================
baseline_mask = (~affected_mask) & (df['category'] != 'books')
q4_baseline_mean_abs_diff = float(df.loc[baseline_mask, 'abs_diff'].mean())

print("\n" + "=" * 70)
print("4. BASELINE SANITY CHECK")
print("=" * 70)
print(f"Baseline Unaffected Non-Books Count: {baseline_mask.sum()}")
print(f"Baseline Mean Absolute Difference: ${q4_baseline_mean_abs_diff:.6f} (~${q4_baseline_mean_abs_diff:.4f})")
print(f"Baseline Max Absolute Difference: ${df.loc[baseline_mask, 'abs_diff'].max():.2f}")

# ============================================================
# Q5: BUG REVERSE ENGINEERING
# ============================================================
print("\n" + "=" * 70)
print("5. REVERSE-ENGINEERED BUG PATTERN")
print("=" * 70)
fragile_exp = df[affected_mask].copy()
fragile_exp['expected_extra'] = np.where(
    fragile_exp['coupon'] == 'SAVE10',
    0.9 * (5.00 + 0.10 * fragile_exp['distance_km']),
    5.00 + 0.10 * fragile_exp['distance_km']
)
fit_error = (fragile_exp['diff'] - fragile_exp['expected_extra']).abs().max()
print(f"Max residual error against formula ($5.00 + $0.10*distance): ${fit_error:.4f}")
print("Pattern: Express surcharge ($5.00 base + $0.10/km) is double-applied for fragile orders!")

# ============================================================
# WRITE answers.json
# ============================================================
answers = {
    "q1_naive_nonzero_count": q1_naive_nonzero_count,
    "q2_affected_count": q2_affected_count,
    "q2_affected_category": q2_affected_category,
    "q3_total_overcharge": round(q3_total_overcharge, 2),
    "q4_baseline_mean_abs_diff": round(q4_baseline_mean_abs_diff, 4)
}

Path(OUTPUT_JSON).write_text(json.dumps(answers, indent=2))
print(f"\nWrote results to {OUTPUT_JSON}:")
print(json.dumps(answers, indent=2))
