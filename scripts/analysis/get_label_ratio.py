import argparse, os
import pandas as pd
from ..utils import CommonUtils

def parse_args():
    parser = argparse.ArgumentParser(
        description="Check the ratio of a given label"
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="Path to the parquet file to be read",
    )
    parser.add_argument(
        "-c",
        "--column_file",
        required=True,
        help="A csv file containing all of the columns to get the ratio of.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="The location where the file would be saved."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="When saving the results, overwrite the output file if it exists. (Default: False)"
    )
    return parser.parse_args()

def save_to_csv(df, path):
    df.to_csv(path, index=False)
    print(f"Saved results to {path}")

args = parse_args()
print(args)

print(f"Reading Column File {args.column_file}")
cols = CommonUtils.readCsvColToList(args.column_file)
print(cols)

print(f"Reading the file: {args.file}")
df = pd.read_parquet(args.file, columns=cols)

print("Get the 0 and 1 counts of each column")
ones = df.sum()
zeroes = (df == 0).sum()

print("Ratio per column")
ratio = ones / df.count()

stats = pd.concat([ones, zeroes, ratio], axis=1, keys=["1", "0", "ratio"])
print(f"Number of Rows: {len(df)}")
print(stats)

if args.output is not None:
    dir_path = os.path.dirname(args.output)
    os.makedirs(dir_path, exist_ok=True)
    
    if args.overwrite is False:
        # Check if file already exists. Skip if exists.
        if os.path.isfile(args.output):
            print(f"The file {args.output} already exists. Skipping save.")
        else:
            save_to_csv(stats, args.output)
    else:
        # If overwrite is True, save regardless.
        save_to_csv(stats, args.output)
