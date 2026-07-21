import argparse, pandas as pd, re
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check all files (label ratios) and total each column (across all chromosomes)."
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Directory containing all the label ratio files to be aggregated.",
    )
    parser.add_argument(
        "-c",
        "--column_file",
        required=True,
        help="A csv file containing all of the columns to get the ratio of.",
    )
    parser.add_argument(
        "--column_name",
        default="features",
        help="The column name of the column file.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="The location where the output files would be saved. (Output Files: per_mark.csv, global.csv)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="When saving the results, overwrite the output file if it exists. (Default: False)",
    )
    return parser.parse_args()

def chrom_sort_key(c):
    m = re.match(r"Chr(\d+)$", c)
    if m:
        return (0, int(m.group(1)))
    return (1, c)   # chrX, chrY, etc.

args = parse_args()
print(args)

print(f"Reading Column File {args.column_file}")
# cols = CommonUtils.readCsvColToList(args.column_file)
marks = pd.read_csv(args.column_file)

# Retrieve the files in the input dir
print(f"Reading Files from {args.input_dir}")
input_dir = Path(args.input_dir)

# Get the Stats per Chromosome
dfs = []
for f in Path(args.input_dir).glob("*.csv"):
    chrom = f.stem
    chrom_stat = pd.read_csv(f)
    
    df = pd.concat([marks, chrom_stat], axis=1)
    df["chromosome"] = f"Chr{chrom}"
    dfs.append(df)

all_df = pd.concat(dfs, ignore_index=True)

# ---- Aggregate Per Mark -----
per_mark = all_df.groupby(args.column_name, as_index=False).agg(
    ones=("1", "sum"), 
    zeros=("0", "sum")
)
per_mark["total"] = per_mark["ones"] + per_mark["zeros"]
per_mark["ratio"] = per_mark["ones"] / per_mark["total"]
per_mark.rename(columns={"ones": "1", "zeros": "0"}, inplace=True)

print("\nSummaries Per Histone Mark")
print(per_mark.to_string(index=False))

# ---- Aggregate Per Chromosome -----
per_chrom = all_df.groupby("chromosome", as_index=False).agg(
    ones=("1", "sum"),
    zeros=("0", "sum")
)

per_chrom["total"] = per_chrom["ones"] + per_chrom["zeros"]
per_chrom["ratio"] = per_chrom["ones"] / per_chrom["total"]
per_chrom.rename(columns={"ones": "1", "zeros": "0"}, inplace=True)

# Sort the chr indexes
per_chrom = (
    per_chrom
    .set_index("chromosome")
    .sort_index(key=lambda idx: idx.map(chrom_sort_key))
    .reset_index()
)

print("\nSummaries Per Chromosome")
print(per_chrom.to_string(index=False))

# ---- Compute Global Totals ----
total_ones = per_mark["1"].sum()
total_zeros = per_mark["0"].sum()
overall_total = total_ones + total_zeros
global_ratio = total_ones / overall_total

global_summary = pd.DataFrame({
    "1": [total_ones], 
    "0": [total_zeros], 
    "total": [overall_total], 
    "ratio": [global_ratio]
})
print("\nOverall Totals")
print(global_summary.to_string(index=False))

# Save to output_dir
if args.output_dir is not None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- SAVE PER MARK ---
    per_mark_path = output_dir / "per_mark.csv"
    if (per_mark_path.exists() and args.overwrite) or (not per_mark_path.exists()):
        per_mark.to_csv(per_mark_path, index=False)
        print(f"Per Mark results is saved at {per_mark_path}")
    else:
        print(f"{per_mark_path} already exists. Skipping save.")

    # --- SAVE PER CHROM ---
    chrom_path = output_dir / "per_chrom.csv"
    if (chrom_path.exists() and args.overwrite) or (not chrom_path.exists()):
        per_chrom.to_csv(chrom_path, index=False)
        print(f"Per Chromosome results is saved at {chrom_path}")
    else:
        print(f"{chrom_path} already exists. Skipping save.")

    # --- SAVE GLOBAL TOTALS ---
    global_path = output_dir / "global.csv"
    if (global_path.exists() and args.overwrite) or (not global_path.exists()):
        global_summary.to_csv(global_path, index=False)
        print(f"Global results is saved at {global_path}")
    else:
        print(f"{global_path} already exists. Skipping save.")
