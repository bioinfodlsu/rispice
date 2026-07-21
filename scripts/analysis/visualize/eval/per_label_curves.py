import argparse
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.metrics import auc
import seaborn as sns
import matplotlib.pyplot as plt

from ....constants import HISTONE_MARKS

OPTIONS = ["roc", "prc"]
ROC_FILES = ["fpr", "tpr", "roc_thresholds"]
PRC_FILES = ["precision", "recall", "prc_thresholds"]

ROC_LABELS = ["False Positive Rate", "True Positive Rate"]
PRC_LABELS = ["Recall", "Precision"]

TICKS = [0.0, 0.25, 0.5, 0.75, 1.0]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a matrix containing models as columns and labels as rows."
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Directory containing all the curve directories.",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="The location where the output files would be saved.",
    )
    parser.add_argument(
        "-m",
        "--metric",
        required=True,
        help="The curve to be processed. (Options: roc, prc)",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="The title of the graph. (Default: *output_filename*)",
    )
    
    return parser.parse_args()

def load_roc(label_dir):
    """Returns the False Positive Rate (x), True Positive Rate (y), and AUC"""
    fpr = np.load(label_dir / "fpr.npy")
    tpr = np.load(label_dir / "tpr.npy")
    auc_val = auc(fpr, tpr)
    
    return fpr, tpr, auc_val

def load_prc(label_dir):
    """Returns the Recall (x), Precision (y), and AUC"""
    recall = np.load(label_dir / "recall.npy")
    precision = np.load(label_dir / "precision.npy")
    auc_val = auc(recall, precision)
    
    return recall, precision, auc_val

def downsample(x, y, max_points=2000):
    if len(x) <= max_points:
        return x, y
    idx = np.linspace(0, len(x) - 1, max_points).astype(int)
    return x[idx], y[idx] 

args = parse_args()
print(args)

# Set Paths
input_dir = Path(args.input_dir)
output_file = Path(args.output_file)

# Check if metric is valid
if not args.metric.lower() in OPTIONS:
    raise ValueError(f"metric arg {args.metric} is invalid. (Options: roc, prc)")


dfs = []
auc_map = {}
# Load the data
print(f"Loading data from {input_dir}...")
for mark in HISTONE_MARKS:
    print(f"**{mark}")
    mark_dir = input_dir / mark
    
    if args.metric == "roc":
        X, Y, auc_val = load_roc(mark_dir)
    else:
        X, Y, auc_val = load_prc(mark_dir)
    
    X, Y = downsample(X, Y, 2000)
    print(len(X))
    print(len(Y))
    
    df = pd.DataFrame({
        "x": X,
        "y": Y,
        "mark": mark
    })
    dfs.append(df)
    auc_map[mark] = auc_val
        
all_df = pd.concat(dfs, ignore_index=True)
print(all_df)

sorted_marks = sorted(auc_map, key=auc_map.get, reverse=True)

# plot
print(f"Plotting the data...")
sns.set_theme(style="darkgrid", font="Open Sans")
plt.figure(figsize=(10, 6))

ax = sns.lineplot(
    data=all_df,
    x='x',
    y='y',
    hue='mark',
    hue_order=sorted_marks,
    estimator=None,
    errorbar=None,
    linewidth=2
)

x_label = ROC_LABELS[0] if args.metric == "roc" else PRC_LABELS[0]
y_label = ROC_LABELS[1] if args.metric == "roc" else PRC_LABELS[1]

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xticks(TICKS)
ax.set_yticks(TICKS)

ax.set_xlabel(x_label, fontweight="semibold")
ax.set_ylabel(y_label, fontweight="semibold")

title = args.title if args.title else output_file.stem
ax.set_title(title, fontweight="semibold")

ax.legend(title="Histone Mark")

if args.metric == "roc":
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5)

# modify the labels
handles, labels = ax.get_legend_handles_labels()
new_labels = [
    f"{label} (AUC={auc_map[label]:.3f})"
    for label in labels
]
ax.legend(
    handles, 
    new_labels, 
    title="Histone Mark",
    loc="upper left",
    bbox_to_anchor=(1.02, 1.0),
    frameon=False
)

# Save to file
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
    