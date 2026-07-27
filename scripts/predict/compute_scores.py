import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from ..helper import get_features

MODES = ["diff", "abs_diff", "log_odds"]

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.predict.compute_scores",
        description=(
            "Compute per-feature and overall scores"
            "from predicted chromatin feature probabilities."
        ),
    )

    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help=(
            "Directory containing the predicted probabilities "
            "(ref.tsv and alt.tsv)."
        ),
    )

    parser.add_argument(
        "-o",
        "--output_dir",
        help=(
            "Directory where the computed scores will be written. "
            "(default: input directory)"
        ),
    )

    parser.add_argument(
        "-m",
        "--mode",
        help=(
            "Method for computing per-feature effect scores. "
            "Options: diff, abs_diff, log_odds."
        ),
    )

    parser.add_argument(
        "-f",
        "--fname",
        help=(
            "Output filename. "
            "(default: scores_<mode>.tsv)"
        ),
    )

    parser.add_argument(
        "--features_path",
        default="features.csv",
        help=(
            "CSV file listing the chromatin features in the expected output "
            "order. (default: features.csv)"
        ),
    )

    return parser.parse_args()

def diff(alt_probs, ref_probs, abs=False):
    """Compute for the Difference between ALT and REF predictions"""
    delta = alt_probs - ref_probs
    return np.abs(delta) if abs else delta  # Absolute value if abs

def log_odds(alt_probs, ref_probs):
    """Compute for the Log Odds Difference between the ALT and REF predictions"""
    alt_odds = np.log(alt_probs / (1 - alt_probs))
    ref_odds = np.log(ref_probs / (1 - ref_probs))
    return alt_odds - ref_odds

args = parse_args()
print(args)

FEATURES = get_features(args.features_path)

if args.mode not in MODES:
    raise ValueError(f"{args.mode} not valid. Select from {MODES} options")

INPUT_DIR = Path(args.input_dir)
OUTPUT_DIR = Path(args.output_dir) if not args.output_dir is None else INPUT_DIR

print(f"Reading files at {INPUT_DIR}...")
ref_probs = pd.read_csv(INPUT_DIR / "ref.tsv", sep="\t").to_numpy()
alt_probs = pd.read_csv(INPUT_DIR / "alt.tsv", sep="\t").to_numpy()

print("Computing Delta Scores...")
if args.mode == "diff":
    print("**Difference of ALT and REF")
    delta_scores = diff(alt_probs, ref_probs)
elif args.mode == "abs_diff":
    print("**Absolute Difference of ALT and REF")
    delta_scores = diff(alt_probs, ref_probs, abs=True)
elif args.mode == "log_odds":
    print("**Log Odds Difference of ALT and REF")
    delta_scores = log_odds(alt_probs, ref_probs)
else:
    raise ValueError(f"{args.mode} not valid. Select from {MODES} options")

df = pd.DataFrame(data=delta_scores, columns=FEATURES)
df["Variant"] = np.linalg.norm(delta_scores, axis=1)

# Make Path
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fname = f"{args.fname}.tsv" if args.fname else f"scores_{args.mode}.tsv"
output_path = OUTPUT_DIR / fname
print(f"Saving results to {output_path}")
df.to_csv(output_path, sep="\t", index=False)