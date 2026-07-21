import argparse, pandas as pd, re
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Check all files (label ratios) and generate a matrix of label ratios (across all chromosomes)."
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
        required=True,
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
    chrom = f.stem  # Get chrom name
    df = pd.read_csv(f)
    df = pd.concat([marks, df], axis=1)
    df["chromosome"] = f"Chr{chrom}"
    dfs.append(df)

all_df = pd.concat(dfs, ignore_index=True)

# Process the results per histone mark
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

for mark, df_mark in all_df.groupby(args.column_name):
    # Rows = chromosomes
    print(f"Processing {mark}...")
    table = (
        df_mark
        .set_index("chromosome")[["1", "0", "ratio"]]
        .sort_index(key=lambda idx: idx.map(chrom_sort_key))
    )
    print(table)
    
    # Save
    output_file = output_dir / f"{mark}.csv"
    if (output_file.exists() and args.overwrite) or (not output_file.exists()):
        table.to_csv(output_file)
        print(f"Matrix is saved at {output_file}")
    else:
        print(f"{output_file} already exists. Skipping save.")