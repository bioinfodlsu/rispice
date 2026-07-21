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
        "-t",
        "--thresholds",
        required=True,
        help="Computed genome-wide thresholds.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Save the results to the dir",
    )
    parser.add_argument(
        "-s",
        "--significance",
        default=0.1,
        type=float,
        help="Genome-wide Significance Level to use. (default: 0.1)"
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

mutageneis_df = pd.read_csv(args.input, sep="\t")

df = mutageneis_df.copy()
df["max_effect"] = df[BASES].abs().max(axis=1)
print("\nin silico saturated mutagenesis analysis results")
print(df)

threshold_df = pd.read_csv(args.thresholds, sep="\t")
threshold = threshold_df[threshold_df["significance_lvl"] == args.significance].to_dict(orient='records')[0]
print("significance threshold ({0}): {1}".format(args.significance, threshold["score"]))

# create is_significant matrix for bases
sig_matrix = df[BASES].abs() >= threshold["score"]
print("\ncreated significant matrix (per base)")
print(sig_matrix)

# Mark Significant (Based on position score)
sig_cumul = df[df["max_effect"] >= threshold["score"]]

print("\nsignificant coordinates based on max position score")
print(sig_cumul)


# # Setup output_dir
output_path = Path(args.output_dir)
output_path.mkdir(parents=True, exist_ok=True)

sig_matrix.to_csv(output_path / "genomewide_sig_matrix.tsv", sep="\t", index=False)
sig_cumul.to_csv(output_path / "genomewide_sig_loci.tsv", sep="\t", index=False)
print(f"Saved results to {output_path}")