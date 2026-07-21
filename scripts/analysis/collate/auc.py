import argparse
import pandas as pd
from ...constants import HISTONE_MARKS
from pathlib import Path

OPTIONS = ["auprc", "auroc"]
PREFIX = "eval"
LABELS = HISTONE_MARKS

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract and create a json file containing a model's best metrics."
    )
    parser.add_argument(
        "-i",
        "--input_file",
        required=True,
        help="The file containing the best metrics for all models for the iteration.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="The directory where the output would be placed.",
    )
    parser.add_argument(
        "--output_fname",
        help="The filename of the output. (Default: *metric*.tsv)",
    )
    parser.add_argument(
        "-m",
        "--metric",
        required=True,
        help="Select the metric to be processed. (Options: auroc, auprc)",
    )
    parser.add_argument(
        "--sort_desc",
        action="store_true",
        help="Sort the result to be descending on average per label",
    )
    
    return parser.parse_args()

def rename_dict(metric, prefix=PREFIX, labels=LABELS):
    names = {}
    for label in labels:
        col = f"{prefix}_{metric}_{label}"
        names[col] = label
    return names

args = parse_args()
print(args)

# Check if metric is valid
if not args.metric.lower() in OPTIONS:
    raise ValueError(f"metric arg {args.metric} is invalid. (Options: auroc, auprc)")

# Get all columns to process
columns = ["model"]
for label in LABELS:
    columns.append(f"{PREFIX}_{args.metric}_{label}")

# Load Data
df = pd.read_csv(args.input_file, sep="\t")[columns]
df = df.rename(columns=rename_dict(args.metric))

# Rotate
df = df.set_index("model").T
df.columns.name = None

# Sort in Desc if flagged
if args.sort_desc:
    df = (
        df
        .assign(mean=df.mean(axis=1))
        .sort_values("mean", ascending=False)
    )
    df.drop(columns="mean", inplace=True)
    
# Print
df = df.reset_index(names="histone_marks")
print(df)

# Save to output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_fname = args.output_fname if args.output_fname else args.metric
output_path = output_dir / f"{output_fname}.tsv"
df.to_csv(output_path, sep="\t", index=False)
print(f"Best Metrics of All Models saved to {output_path}")