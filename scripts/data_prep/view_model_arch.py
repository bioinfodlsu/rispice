import argparse
from ..finetuning.train_utils import load_model, count_model_params, print_model_params


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load and view a downloaded Model's architecture"
    )
    parser.add_argument(
        "-m",
        "--model",
        required=True,
        help="Directory of the base model used during training.",
    )

    parser.add_argument("--automodel", action="store_true")

    return parser.parse_args()


args = parse_args()
print(args)

# Load the models
print(f"Loading model from {args.model}")
model, _ = load_model(args.model, args.automodel)
print(f"Loaded the {model}")

base_cnts = count_model_params(model)
print_model_params(base_cnts, "\nBase Model Parameter Counts")
