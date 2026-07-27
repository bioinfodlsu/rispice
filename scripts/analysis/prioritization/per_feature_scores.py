import argparse, pandas as pd
from pathlib import Path
from ...helper import get_features

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.analysis.prioritization.per_feature_scores",
        description="Generate the per-feature scores sorted by Overall Score."
    )

    parser.add_argument(
        "--scores",
        required=True,
        help="Path to the scores.tsv file.",
    )
    parser.add_argument(
        "--snp_list",
        required=True,
        help="Path to the snp_list.tsv file.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where the output file will be saved.",
    )
    parser.add_argument(
        "--output_fn",
        default="per_feature_scores.tsv",
        help="Name of the output file. (Default: per_feature_scores.tsv)",
    )
    parser.add_argument(
        "--use_existing_id",
        action="store_true",
        help="Use the existing IDs from the SNP list instead of generating new variant IDs.",
    )
    parser.add_argument(
        "--metric",
        default="Variant",
        help="Column used to rank the variants. (Default: Variant)",
    )
    parser.add_argument(
        "--top",
        type=int,
        help="Number of top-ranked variants to include in the output.",
    )
    parser.add_argument(
        "--positions",
        help="Path to a TSV file containing variant positions to retain. The file must contain a column named 'pos'.",
    )
    parser.add_argument(
        "--features_path",
        default="features.csv",
        help="Path to the CSV file listing the features to include. (Default: features.csv)",
    )

    return parser.parse_args()

args = parse_args()
print(args)

LABELS = get_features(args.features_path)

# Extract and merge the snp list and scores
df = pd.concat([
        pd.read_csv(args.snp_list, sep="\t"),
        pd.read_csv(args.scores, sep="\t"),
    ], axis=1)

# Sort it based on the Variant
df.sort_values(by=args.metric, ascending=False, inplace=True)

# Get the top N of the data
if args.top:
    df = df[:args.top]

if not args.use_existing_id:
    df["id"] = "Chr" + df["chrom"].astype(str) + ":" + df["pos"].astype(str) + "_" + df["ref"] + df["alt"]

# filter if needed
if args.positions:
    filter_df = pd.read_csv(args.positions, sep="\t")
    df = df[df["pos"].isin(filter_df["pos"])]

# Retain the relevant columns
cols = ["id"] + LABELS
df = df[cols]
print(df)

# Setup output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

fname = f"per_feature_scores_top{args.top}.tsv" if args.top else args.output_fn

output_path = output_dir / fname
df.to_csv(output_path, sep="\t", index=False)
print(f"Saved Per-Feature Scores to {output_path}")