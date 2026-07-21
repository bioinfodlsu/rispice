import argparse
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef
)
from ...constants import HISTONE_MARKS
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute for the ROC and PRC curves given logits and labels."
    )
    parser.add_argument(
        "--logits",
        required=True,
        help="logits .npy file.",
    )
    parser.add_argument(
        "--labels",
        required=True,
        help="labels .npy file.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where the threshold metrics would be stored.",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        required=True,
        type=float,
        help="the threshold when computing predictions.",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

# load the numpy files
print(f"Loading logits from {args.logits}")
logits = np.load(args.logits)

print(f"Applying sigmoid to logits. Computing Per-Label Predictions.")
probs = expit(logits)
pred = (probs >= args.threshold).astype(int)
print(pred.shape)

print(f"Loading labels from {args.labels}")
labels = np.load(args.labels)
print(labels.shape)

# Get the predictions
result = []
print(f"Processing {len(HISTONE_MARKS)} labels")
for i, mark in enumerate(HISTONE_MARKS):
    print(f"**{mark}")
    y_true = labels[:, i]
    y_hat = pred[:, i]
    
    positives = y_true.sum()
    negatives = len(y_true) - positives
    
    # Skip degenerate labels
    if positives == 0 or negatives == 0:
        result.append({
            "threshold": args.threshold,
            "mark": mark,
            "accuracy": np.nan,
            "precision": np.nan,
            "recall": np.nan,
            "f1": np.nan,
            "mcc": np.nan,
            "pos_cnt": int(positives),
            "neg_cnt": int(negatives),
            "tot_cnt": int(positives) + int(negatives)
        })
        continue
    
    result.append({
        "threshold": args.threshold,
        "mark": mark,
        "accuracy": accuracy_score(y_true, y_hat),
        "precision": precision_score(y_true, y_hat, zero_division=0),
        "recall": recall_score(y_true, y_hat, zero_division=0),
        "f1": f1_score(y_true, y_hat, zero_division=0),
        "mcc": matthews_corrcoef(y_true, y_hat),
        "pos_cnt": int(positives),
        "neg_cnt": int(negatives),
        "tot_cnt": int(positives) + int(negatives)
    })
    
df = pd.DataFrame(result)
print(df)

# Setup output_dir
output_dir = Path(args.output_dir)
output_path = output_dir / "threshold" / f"{int(args.threshold * 100)}.tsv"
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, sep="\t", index=False)
print(f"Saved thresholded-metrics (t={args.threshold}) in {output_path}")