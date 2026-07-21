import argparse
import pandas as pd
from pathlib import Path

CLOSEST_COLS = ["chrA", "startA", "endA", "chrB", "startB", "endB", "distance"]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute for the label co-occurrence in a file."
    )
    parser.add_argument(
        "-f",
        "--feature",
        help="The Chromatin Feature being processed. This will be the filename output.",
    )
    parser.add_argument(
        "-d",
        "--dir",
        help="Directory containing all distance files (processed via bedtools closest).",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Where the distribution data would be saved.",
    )
    
    return parser.parse_args()

def clean_stem(f_stem):
    """Remove the `vs_` in the filename"""
    return f_stem.partition("_")[2]
    

args = parse_args()
print(args)

# Get files
dir_path = Path(args.dir)
files = list(dir_path.rglob("*.tsv"))

rows = []
for f in files:
    feature = clean_stem(f.stem)
    df = pd.read_csv(f, sep="\t", header=None, names=CLOSEST_COLS)
    
    dist = df.iloc[:, -1]
    invalid = (dist < 0).sum()  # those with -1 (no peaks close enough)
    dist = dist[dist >= 0]
    
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
        
        "invalid": invalid
    }
    
    rows.append(row)
    
summary = pd.DataFrame(rows)
print(summary)

# Save output
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

summary_path = output_dir / f"{args.feature}.tsv"
summary.to_csv(summary_path, sep="\t", index=False)
print(f"Saved summary to {summary_path}")