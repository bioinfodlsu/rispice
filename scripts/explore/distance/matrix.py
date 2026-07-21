import argparse
import pandas as pd
from pathlib import Path
from ...constants import HISTONE_MARKS

FEATURES = HISTONE_MARKS

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Matrix for all Features given distributions in the dir."
    )
    parser.add_argument(
        "-d",
        "--dir",
        help="Directory containing all distribution stats (generated via dist.py).",
    )
    parser.add_argument(
        "-k",
        "--key",
        help="The metric to get from the distributions for the matrix.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Where the matrix file would be saved.",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

INPUT_DIR = Path(args.dir)
rows = []
for anchor in FEATURES:
    dist = INPUT_DIR / f"{anchor}.tsv"
    
    df = pd.read_csv(dist, sep="\t")
    # Capture feature and median
    d = dict(zip(df["feature"], df[args.key]))
    d[anchor] = 0   # set self to zero
    d["feature"] = anchor
    rows.append(d)

matrix = pd.DataFrame(rows).set_index("feature")
matrix = matrix.reindex(columns=FEATURES)
print(matrix)

# Save output
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

matrix.to_csv(output_path, sep="\t")
print(f"Saved matrix to {output_path}")
