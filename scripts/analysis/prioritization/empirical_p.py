import argparse
import pandas as pd
import numpy as np
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.analysis.prioritization.empirical_p",
        description="Compute the empirical p-values of scores given background."
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
        "-o",
        "--output_dir",
        required=True,
        help="Path where the file will be saved to.",
    )
    parser.add_argument(
        "--output_fn",
        help="Name of the output file. (Default: { metric }.tsv)",
    )
    parser.add_argument(
        "--metric",
        default="Variant",
        help="Column whose p-values would be computed. (Default: Variant)",
    )
    parser.add_argument(
        "--use_existing_id",
        action="store_true",
        help="Use the existing IDs from the SNP list instead of generating new variant IDs.",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

# Load the SNPs and Scores
snps_df = pd.read_csv(args.snp_list, sep="\t")
scores_df = pd.read_csv(args.scores, sep="\t")[args.metric]
df = pd.concat([snps_df, scores_df], axis=1)
print(f"# of SNPs: {len(df):,}")

# Load the background scores
bg_scores = np.abs(
    pd.read_csv(args.bg_scores, sep="\t")[args.metric].values
)
sorted_bg = np.sort(bg_scores)
n_bg = len(sorted_bg)
print(f"# of Background SNPs: {n_bg:,}")

# Vectorized Calc of empirical p-vals
snp_scores = np.abs(df[args.metric].to_numpy())

counts_above = n_bg - np.searchsorted(sorted_bg, snp_scores, side="right")

df["p-value"] = (counts_above + 1) / (n_bg + 1) # Consider case where counts_above is 0
df.sort_values(by="p-value", inplace=True)

# Format to expected result
if not args.use_existing_id:
    df["id"] = "Chr" + df["chrom"].astype(str) + ":" + df["pos"].astype(str) + "_" + df["ref"] + df["alt"]

df.rename(columns={args.metric: "score"}, inplace=True)
df = df[["id", "score", "p-value"]]
print(df)

# Save to file
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

if not args.output_fn:
    output_path = output_dir / f"{args.metric}.tsv" 
else:
    output_path = output_dir / args.output_fn

df.to_csv(output_path, sep="\t", index=False)
print(f"Saved to {output_path}")