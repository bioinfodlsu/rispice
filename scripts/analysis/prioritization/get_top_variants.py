import argparse, pandas as pd
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Sort the Top Variants given the Variant Scores."
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
        help="Start base.",
    )
    parser.add_argument(
        "--output_fn",
        default="top_variants.tsv",
        help="File Name of the output",
    )
    parser.add_argument(
        "--use_existing_id",
        action="store_true",
        help="Use the existing ID within the SNP List for the labels",
    )
    parser.add_argument(
        "--metric",
        default="Variant",
        help="The metric that would be used for sorting the variants. (Default: Variant)",
    )
    parser.add_argument(
        "--top",
        type=int,
        help="The number of variants to be included in the list",
    )
    parser.add_argument(
        "--filter",
        help="Only include variants in the given list (positions). This is a path to a tsv file.",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

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
if args.filter:
    filter_df = pd.read_csv(args.filter, sep="\t")
    df = df[df["pos"].isin(filter_df["pos"])]

# Retain the relevant columns
df = df[["id", args.metric]]
print(df)

# Setup output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

fname = f"top{args.top}_variants.tsv" if args.top else args.output_fn

output_path = output_dir / fname
df.to_csv(output_path, sep="\t", index=False)
print(f"Saved SNP List to {output_path}")
