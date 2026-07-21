import argparse
import pandas as pd
import numpy as np
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute the Empirical P-values of scores given background."
    )
    parser.add_argument(
        "--scores",
        required=True,
        help="Path to the scores file.",
    )
    parser.add_argument(
        "--snp_list",
        required=True,
        help="Path to the snp_list file.",
    )
    parser.add_argument(
        "--bg_scores",
        required=True,
        help="Path to the scores file for background.",
    )
    parser.add_argument(
        "--key",
        default="Variant",
        help="Key to the metric to be computed a p-value for.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the file will be saved to.",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

# Load the SNPs and Scores
snps_df = pd.read_csv(args.snp_list, sep="\t")
scores_df = pd.read_csv(args.scores, sep="\t")[args.key]
df = pd.concat([snps_df, scores_df], axis=1)
print(f"# of SNPs: {len(df):,}")

# Load the background scores
bg_scores = pd.read_csv(args.bg_scores, sep="\t")[args.key].values
sorted_bg = np.sort(bg_scores)
n_bg = len(sorted_bg)
print(f"# of Background SNPs: {n_bg:,}")

# Vectorized Calc of empirical p-vals
snp_scores = np.array(df[args.key])
counts_above = n_bg - np.searchsorted(sorted_bg, snp_scores, side="right")

df["p-value"] = (counts_above + 1) / (n_bg + 1) # Consider case where counts_above is 0
df.sort_values(by="p-value", inplace=True)
print(df)

# Save to file
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(args.output, sep="\t", index=False)
print(f"Saved to {output_path}")