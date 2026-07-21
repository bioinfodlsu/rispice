import argparse, json
from ..train_utils import compute_training_steps
from pathlib import Path
from datasets import load_from_disk

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate the Parameter JSON File to be used for the train.py script."
    )

    parser.add_argument(
        "-m",
        "--model",
        required=True,
        help="Path where the local model is stored",
    )
    parser.add_argument(
        "--train",
        required=True,
        help="Path to train dataset",
    )
    parser.add_argument(
        "--val",
        required=True,
        help="Path to validation dataset",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="The dir and filename of the json file to be saved.",
    )

    # Trainer hyperparams
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--epoch", type=int, default=3)
    
    parser.add_argument("--eval_batch_size", type=int, default=8)

    parser.add_argument("--grad_accum", type=int, default=1)
    parser.add_argument("--warmup_ratio", type=float, default=0.05)
    parser.add_argument("--eval_accumulation_steps", type=int, default=5)

    # Best Model
    parser.add_argument("--metric_for_best_model", default="eval_loss")
    parser.add_argument("--greater_is_better", default=False)
    parser.add_argument("--save_total_limit", type=int, default=5)

    # Early Stopping
    parser.add_argument("--early_stopping_patience", type=int, default=3)
    parser.add_argument("--early_stopping_threshold", type=float, default=0.0)

    # Performance
    parser.add_argument("--dataloader_num_workers", type=int, default=4)

    return parser.parse_args()

def print_params(train_params, header="Training Parameters/Details:"):
    print(header)
    for k, v in train_params.items():
        print(f"  {k}: {v}")

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

# Get Train Dataset for reference
train_ds = load_from_disk(args.train)
val_ds = load_from_disk(args.val)

# Compute Training Steps
print(f"**Computing Training Steps for {args.train}")
steps_dict = compute_training_steps(
        num_samples=len(train_ds),
        batch_size=args.batch_size,
        num_epochs=args.epoch,
        grad_accum=args.grad_accum
    )

params = {}

print("**Defining Training Arguments")
# Define Required Arguments
# Required Arguments
params["model"] = args.model
params["train_path"] = args.train
params["val_path"] = args.val

# Trainer Hyperparameters
params["batch_size"] = args.batch_size
params["learning_rate"] = args.learning_rate
params["weight_decay"] = args.weight_decay
params["epoch"] = args.epoch
    
params["grad_accum"] = args.grad_accum          # Gradient Accumulation Steps
params["warmup_ratio"] = args.warmup_ratio

params["eval_batch_size"] = args.eval_batch_size
params["eval_accumulation_steps"] = args.eval_accumulation_steps
params["dataloader_num_workers"] = args.dataloader_num_workers

# Trainer Arguments
params["save_total_limit"] = args.save_total_limit
params["early_stopping_patience"] = args.early_stopping_patience
params["early_stopping_threshold"] = args.early_stopping_threshold
params["metric_for_best_model"] = args.metric_for_best_model
params["greater_is_better"] = args.greater_is_better

# Training Process
params["train_size"] = len(train_ds)
params["val_size"] = len(val_ds)
params["steps_per_epoch"] = steps_dict["steps_per_epoch"]
params["total_steps"] = steps_dict["total_steps"]
params["logging_steps"] = steps_dict["logging_steps"]
params["eval_steps"] = steps_dict["eval_steps"]
params["save_steps"] = steps_dict["save_steps"]

print_params(params, "\nTraining Parameters")

# Setup Output Path
output_path = Path(args.output_file)

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path = ensure_json_extension(output_path)

save_params(output_path, params)