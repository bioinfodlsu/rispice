import argparse, pandas as pd
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.analysis.prioritization.rank",
        description="Rank variants based on their RiSPICE scores."
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
        default="top_variants.tsv",
        help="Name of the output file. (Default: top_variants.tsv)",
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
        "--positions",
        help=(
            "Path to a TSV file containing variant positions to retain. "
            "The file must contain a column named 'pos'."
        ),
    )
    
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument(
        "--top",
        type=int,
        help="Number of top-ranked variants to include in the output.",
    )
    
    group.add_argument(
        "-t",
        "--thresholds",
        help=(
            "Path to the thresholds.tsv file containing empirical "
            "genome-wide significance thresholds. "
            "Providing this will filter the variants based on its significance."
        ),
    )
    parser.add_argument(
        "-s",
        "--significance",
        default=0.05,
        type=float,
        help=(
            "Significance level of variants to retain. "
            "(default: %(default)s)."
        ),
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

if args.thresholds:
    threshold_df = pd.read_csv(args.thresholds, sep="\t")
    threshold = threshold_df[threshold_df["significance_lvl"] == args.significance].to_dict(orient='records')[0]
    print("significance threshold ({0}): {1}".format(args.significance, threshold["score"]))
    
    # filter df based on the threshold
    print(f"Total SNPs: {len(df)}")
    df = df[df[args.metric] >= threshold["score"]]
    print(f"Significant SNPs (threshold={args.significance}): {len(df)}")

if not args.use_existing_id:
    df["id"] = "Chr" + df["chrom"].astype(str) + ":" + df["pos"].astype(str) + "_" + df["ref"] + df["alt"]

# filter if needed
if args.positions:
    filter_df = pd.read_csv(args.positions, sep="\t")
    df = df[df["pos"].isin(filter_df["pos"])]

# Retain the relevant columns
df = df[["id", args.metric]]
print(df)

# Setup output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

if args.top:
    fname = f"top{args.top}_variants.tsv"
elif args.thresholds:
    fname = f"sig_variants_{int(args.significance*100)}.tsv"
else:
    fname = args.output_fn

output_path = output_dir / fname
df.to_csv(output_path, sep="\t", index=False)
print(f"Saved SNP List to {output_path}")
