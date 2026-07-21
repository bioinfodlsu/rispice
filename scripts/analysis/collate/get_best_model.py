import argparse, json
import pandas as pd
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract and create a json file containing a model's best metrics."
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Directory containing the collated logs of the model.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="The directory where the output would be placed.",
    )
    parser.add_argument(
        "-b",
        "--best_step",
        required=True,
        type=int,
        help="Step number of the Best Checkpoint of the trained model.",
    )
    parser.add_argument(
        "-f",
        "--file_name",
        default="eval_logs.tsv",
        help="Filename in the directory to be accessed. (Default: eval_logs.tsv)",
    )
    parser.add_argument(
        "--output_fname",
        default="best_model.json",
        help="The filename of the output. (Default: best_model.json)",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

input_path = Path(args.input_dir) / args.file_name

df = pd.read_csv(input_path, sep="\t")

best_metrics = df[df["step"] == args.best_step].to_dict(orient='records')[0]

# Save to output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / args.output_fname
with open(output_path, "w") as f:
    json.dump(best_metrics, f, indent=2)
print(f"Extracted and saved the best metrics to {output_path}")