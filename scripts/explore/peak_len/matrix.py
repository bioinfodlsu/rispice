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
CHROMS = get_chroms()
rows = []
for feature in FEATURES:
    input_path = input_dir / f"{feature}_consensus_merged.bed"
    print(input_path)
    
    df = pd.read_csv(input_path, sep="\t", header=None, names=["chr", "start", "end"])
    df = df.sort_values(["chr","start"])
    
    # Remove chr outside of 1-12
    df = df[df["chr"].isin(CHROMS)]
    
    # peak width
    df["width"] = df["end"] - df["start"]
    metric = df["width"]
    
    row = {
        "feature": feature,
        "count": len(metric),
        "mean": metric.mean(),
        "median": metric.median(),    # 50th percentile
        "std": metric.std(),
        "min": metric.min(),
        "max": metric.max(),
        "p25": metric.quantile(0.25),
        "p75": metric.quantile(0.75),
        "p90": metric.quantile(0.90),
        "p95": metric.quantile(0.95),
        "p99": metric.quantile(0.99),
        
        "pct_100bp": (metric <= 100).mean(),
        "pct_250bp": (metric <= 250).mean(),
        "pct_500bp": (metric <= 500).mean(),
        "pct_1kb": (metric <= 1000).mean(),
        "pct_2kb": (metric <= 2000).mean(),
        "pct_5kb": (metric <= 5000).mean(),
        "pct_10kb": (metric <= 10000).mean(),
    }
    
    rows.append(row)
    
summary = pd.DataFrame(rows)
print(summary)

# Save output
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

summary.to_csv(output_path, sep="\t", index=False)
print(f"Saved results to {output_path}")
