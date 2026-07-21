import argparse
import pandas as pd
from scipy.stats import zscore
from ...constants import BASES
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Given a tsv file containing the Mutagenesis Analysis results, compute for the `z_score` per base."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the mutagenesis analysis dataframe file.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Save the results to the file",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        default=2,
        type=int,
        help="z-score threshold for significance. (default: 2)"
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

mutageneis_df = pd.read_csv(args.input, sep="\t")

df = mutageneis_df.copy()

print("\nin silico saturated mutagenesis analysis results")
print(df)

# Compute z-scores
df[BASES] = df[BASES].apply(zscore)
df["cumulative"] = zscore(df["cumulative"])

print("\nz-scores per base and cumulative")
print(df)

# Mark Significant
threshold = args.threshold
sig_cumul = df[abs(df["cumulative"]) > threshold]

print("\nsignificant coordinates based on cumulative score")
print(sig_cumul)

# create is_significant matrix for bases
sig_matrix = df[BASES].abs() > threshold
print("\ncreated significant matrix (per base)")

# Setup output_dir
output_path = Path(args.output_dir)
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path / "z_score.tsv", sep="\t", index=False)
sig_matrix.to_csv(output_path / "significant_matrix.tsv", sep="\t", index=False)
sig_cumul.to_csv(output_path / "significant_loci.tsv", sep="\t", index=False)
print(f"Saved results to {output_path}")