import argparse
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_curve, precision_recall_curve, auc
from ...helper import get_features
# from ...constants import HISTONE_MARKS
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
        help="Directory where the roc and prc values would be stored.",
    )
        
    parser.add_argument(
        "--features_path",
        default=".data2/prep/constant/features.csv",
        help="Path to csv file containing the list of all features to process (ensure sorting.).",
    )
    return parser.parse_args()

args = parse_args()
print(args)

FEATURES = get_features(args.features_path)

# load the numpy files
print(f"Loading logits from {args.logits}")
logits = np.load(args.logits)

print(f"Applying sigmoid to logits")
probs = expit(logits)
print(probs.shape)

print(f"Loading labels from {args.labels}")
labels = np.load(args.labels)
print(labels.shape)


# Setup output_dir
output_dir = Path(args.output_dir)
output_path = output_dir / "curves"
output_path.mkdir(parents=True, exist_ok=True)

# Get the probs
auc_val = []
print(f"Processing {len(FEATURES)} labels")
for i, mark in enumerate(FEATURES):
    print(f"**{mark}")
    mark_path = output_path / mark
    mark_path.mkdir(parents=True, exist_ok=True)
    
    y_true = labels[:, i]
    y_score = probs[:, i]
    
    # ROC
    fpr, tpr, roc_thresholds  = roc_curve(y_true, y_score)
    np.save(mark_path / "fpr.npy", fpr)
    np.save(mark_path / "tpr.npy", tpr)
    np.save(mark_path / "roc_thresholds.npy", roc_thresholds)

    # PRC
    precision, recall, prc_thresholds  = precision_recall_curve(y_true, y_score)
    np.save(mark_path / "precision.npy", precision)
    np.save(mark_path / "recall.npy", recall)
    np.save(mark_path / "prc_thresholds.npy", prc_thresholds)

    # Save AUC values
    auc_val.append({
        "mark": mark,
        "auroc": auc(fpr, tpr),
        "auprc": auc(recall, precision)
    })
    
df = pd.DataFrame(auc_val)
print(df)
df.to_csv(output_path / "auc.tsv", sep="\t", index=False)
print(f"Saved ROC and PRC values in {output_path}")
