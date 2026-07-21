import argparse
import pandas as pd
from pathlib import Path
from ...constants import HISTONE_MARKS

FEATURES = HISTONE_MARKS

def parse_args():
    parser = argparse.ArgumentParser(
        description="Get the distance distribution between peaks across all features in a dir."
    )
    parser.add_argument(
        "-d",
        "--dir",
        help="Dataset (or parquet file) containing all the labels.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Save the df to this file.",
    )
    
    return parser.parse_args()

def get_chroms():
    chroms = []
    for i in range(1,13):
        chroms.append(f"chr{i}")
    return chroms

def get_feature(stem):
    return stem.split("_")[0]

args = parse_args()
print(args)

input_dir = Path(args.dir)
files = list(input_dir.glob("*.bed"))
CHROMS = get_chroms()

rows = []
for f in files:
    feature = get_feature(f.stem)
    
    df = pd.read_csv(f, sep="\t", header=None, names=["chr", "start", "end"])
    df = df.sort_values(["chr","start"])
    
    # Remove chr outside of 1-12
    df = df[df["chr"].isin(CHROMS)]
    
    df["dist"] = df.groupby("chr")["start"].diff()
    dist = df["dist"].dropna()
    
    row = {
        "feature": feature,
        "count": len(dist),
        "mean": dist.mean(),
        "median": dist.median(),    # 50th percentile
        "std": dist.std(),
        "min": dist.min(),
        "max": dist.max(),
        "p25": dist.quantile(0.25),
        "p75": dist.quantile(0.75),
        "p90": dist.quantile(0.90),
        "p95": dist.quantile(0.95),
        "p99": dist.quantile(0.99),
        
        "pct_100bp": (dist <= 100).mean(),
        "pct_250bp": (dist <= 250).mean(),
        "pct_500bp": (dist <= 500).mean(),
        "pct_1kb": (dist <= 1000).mean(),
        "pct_2kb": (dist <= 2000).mean(),
        "pct_5kb": (dist <= 5000).mean(),
        "pct_10kb": (dist <= 10000).mean(),
    }
    
    rows.append(row)
    
summary = pd.DataFrame(rows)
print(summary)

# Save output
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

summary.to_csv(output_path, sep="\t", index=False)
print(f"Saved results to {output_path}")


