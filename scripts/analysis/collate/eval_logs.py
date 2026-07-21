import argparse, json, pandas as pd
from pathlib import Path

# CONSTANTS
EVAL_LOSS_KEY = "eval_loss"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Given a model directory, extract all Eval logs."
    )
    
    parser.add_argument(
        "-d",
        "--directory",
        required=True,
        help="Directory of the Trained model.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="The directory where the output would be placed.",
    )
    parser.add_argument(
        "-f",
        "--file_name",
        default="eval_metrics.json",
        help="Filename in the directory to be accessed. (Default: eval_metrics.json)",
    )
    parser.add_argument(
        "--output_fname",
        default="eval_logs.tsv",
        help="The filename of the output. (Default: eval_logs.tsv)",
    )
    
    return parser.parse_args()

def loadJSON(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data

def rename_col(col):
    if col in ["step", "epoch"]:
        return col
    if not col.startswith("eval_"):
        return f"eval_{col}"
    return col

args = parse_args()
print(args)

input_file = Path(args.directory) / args.file_name
data = loadJSON(input_file)

entries = {}
for log in data:
    # Skip if not eval log
    if not EVAL_LOSS_KEY in log:
        continue
    
    # Add to entries for every log
    # Overwrite repeating logs (case: Resuming training after stoppage)
    entries[log["step"]] = log

# print(entries)
df = pd.DataFrame(list(entries.values()))
df = df.rename(columns=rename_col)
print(df)

# Save to output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / args.output_fname
df.to_csv(output_path, sep="\t", index=False)
print(f"Eval Logs saved to {output_path}")