import argparse, os, pandas as pd
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Label Processing given a dir containing coverage files of an Annotation."
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Path to the dir containing all the coverage files to be processed.",
    )
    parser.add_argument(
        "-c",
        "--column",
        default="percent_covered",
        help="The column of the coverage files that will be referred to.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="The file where the output will be stored. The parent directories will be automatically created.",
    )
    parser.add_argument(
        "--stats_path",
        required=True,
        help="The file where the stats will be stored. The parent directories will be automatically created.",
    )
    parser.add_argument(
        "--coverage_threshold",
        type=int,
        default=50,
        help="If the coverage of a sample is greater than or equal to this percent value, the sample's label will be 1. (Default: 50)",
    )
    parser.add_argument(
        "--majority_threshold",
        type=float,
        default=0.5,
        help="If the majority of the samples of an annotation is greater than or equal to this percent value, the mark's overall label will be 1. (Default: 0.5)",
    )
    return parser.parse_args()


args = parse_args()
print(args)

# Retrieve the files in the input dir
files = os.listdir(args.input_dir)
files = [
    os.path.join(args.input_dir, f)
    for f in files
    if os.path.isfile(os.path.join(args.input_dir, f))
]

per_sample_coverage = []
stats = []
# Read each file
for f in files:
    print(f"Processing {f}")
    sample_df = pd.read_csv(
        f, sep="\t", usecols=[args.column], dtype={args.column: "float32"}
    )[args.column]

    # Check whether the sample's pct covered is >= threshold
    mask = sample_df >= args.coverage_threshold

    print(f"{mask.sum():,} / {len(mask):,}")
    per_sample_coverage.append(mask)
    stats.append({
        "file": f,
        "positive": mask.sum(),
        "total": len(mask),
        "prevalence": mask.sum() / len(mask) 
    })

# Create a dataframe for all
df = pd.concat(per_sample_coverage, axis=1)

# Majority
print("Aggregating across all samples...")
majority_result = (
    df.sum(axis=1) >= (args.majority_threshold * len(df.columns))   # simple majority
).astype("int64")

print("Final Labels:")
print(f"{majority_result.sum():,} / {len(majority_result):,}")

# Save the final output
stats.append({
    "file": args.output,
    "positive": majority_result.sum(),
    "total": len(majority_result),
    "prevalence": majority_result.sum() / len(majority_result) 
})


# Save to location
output_path = Path(args.output)
stats_path = Path(args.stats_path)

# Ensure parent dir exists
output_dir = output_path.parent  # parent folder
output_dir.mkdir(parents=True, exist_ok=True)
stats_path.parent.mkdir(parents=True, exist_ok=True)

majority_result.to_csv(output_path, index=False)
print(f"Results are saved to {output_path}")

stats_df = pd.DataFrame(stats)
stats_df.to_csv(stats_path, sep="\t", index=False)
print(f"Saved stats to {stats_path}")