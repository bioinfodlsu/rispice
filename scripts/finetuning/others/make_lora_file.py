import argparse, json
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate the Parameter JSON File to be used for the train.py script."
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="The dir and filename of the json file to be saved.",
    )
    
    parser.add_argument(
        "--target_modules_file",
        default="scripts/finetuning/others/lora_targets.json",
        help="Path containing the possible options for target_modules",
    )
    parser.add_argument(
        "--target_modules_key",
        default="2",
        help="Select via a kay from the target_modules file which target modules will be selected.",
    )
    
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.05)
    
    return parser.parse_args()

def print_params(params, header="LoRA Parameters: "):
    print(header)
    for k, v in params.items():
        print(f"  {k}: {v}")

def load_targets(path):
    with open(path, "r") as f:
        targets = json.load(f)
    return targets

def save_params(params_path, params):
    with open(params_path, "w") as f:
        json.dump(params, f, indent=2)
    print(f"Saved parameters to {params_path}")

def ensure_json_extension(p: Path) -> Path:
    """Forces the path extension to be .json."""
    if p.suffix.lower() != ".json":
        return p.with_suffix(".json")
    return p

args = parse_args()
print(args)

targets = load_targets(args.target_modules_file)

params = {}

# Define Required Arguments
params["rank"] = args.rank
params["alpha"] = args.alpha
params["dropout"] = args.dropout
params["target_modules"] = targets[args.target_modules_key]

print_params(params)

# Setup Output Path
output_path = Path(args.output_file)

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path = ensure_json_extension(output_path)

save_params(output_path, params)