import argparse
import pandas as pd
from pathlib import Path
from ...helper import get_features

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.analysis.prioritization.per_feature_hits",
        description="Acquire significant Per-Feature Scores."
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
        help="Name of the output file. (Default: hits_{sig*100}.tsv)",
    )
    parser.add_argument(
        "-s",
        "--significance",
        default=0.05,
        type=float,
        help=(
            "Significance level to filter "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--thresholds_dir",
        required=True,
        help="Path to the directory containing all thresholds for per-feature scores.",
    )
    parser.add_argument(
        "--features_path",
        default="features.csv",
        help="Path to the CSV file listing the features to include. (Default: features.csv)",
    )
    
    parser.add_argument(
        "--use_existing_id",
        action="store_true",
        help="Use the existing IDs from the SNP list instead of generating new variant IDs.",
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

if not args.use_existing_id:
    df["id"] = "Chr" + df["chrom"].astype(str) + ":" + df["pos"].astype(str) + "_" + df["ref"] + df["alt"]

thresholds_dir = Path(args.thresholds_dir)
sig_hits = []
print(f"Filtering hits based on significance ({args.significance})")
for feature in LABELS:
    # Get threshold for feature
    threshold_df = pd.read_csv(thresholds_dir / f"{feature}.tsv", sep="\t")
    threshold = threshold_df[threshold_df["significance_lvl"] == args.significance].to_dict(orient='records')[0]

    # Get the significant
    sig_df = df[(df[feature].abs() >= threshold["score"])]
    print(f"{feature}: {len(sig_df)} hits")
    temp_df = sig_df[["id"]].copy()
    temp_df["feature"] = feature
    temp_df["score"] = sig_df[feature]
    temp_df = temp_df.reset_index(drop=True)
    sig_hits.append(temp_df)

col_order = ["feature", "id", "score"]
all_sigs_df = pd.concat(sig_hits)
all_sigs_df = all_sigs_df.reindex(columns=col_order)
all_sigs_df.reset_index(drop=True, inplace=True)

# Setup output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

if not args.output_fn:
    fname = f"hits_sig{int(args.significance*100)}.tsv"
else:
    fname = args.output_fn

output_path = output_dir / fname
all_sigs_df.to_csv(output_path, sep="\t", index=False)
print(f"Saved Per-Feature Hits to {output_path}")