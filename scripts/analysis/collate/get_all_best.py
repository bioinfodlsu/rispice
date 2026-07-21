import argparse, json
import pandas as pd
from pathlib import Path
from ...constants import MODEL_KEYS

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract and create a json file containing a model's best metrics."
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Directory containing all the models for a specific iteration.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="The directory where the output would be placed.",
    )
    parser.add_argument(
        "-f",
        "--fname",
        default="best_model.json",
        help="Filename in the directories to be accessed. (Default: best_model.json)",
    )
    parser.add_argument(
        "--output_fname",
        default="all_best.tsv",
        help="The filename of the output. (Default: all_best.tsv)",
    )
    
    return parser.parse_args()

def loadJSON(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data

args = parse_args()
print(args)

data = []
for key in MODEL_KEYS:
    path = Path(args.input_dir) / key / args.fname
    
    dict = { "model": key } | loadJSON(path)
    data.append(dict)
    print(f"Loaded {path}")

df = pd.DataFrame(data)
print(df)

# Save to output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / args.output_fname
df.to_csv(output_path, sep="\t", index=False)
print(f"Best Metrics of All Models saved to {output_path}")
    