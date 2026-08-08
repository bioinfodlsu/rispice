import argparse
import pandas as pd
import numpy as np
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.analysis.visualize.prioritization.mutagenesis_heatmap",
        description="Generate a heatmap from the mutagenesis analysis matrix."
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the mutagenesis analysis matrix TSV file.",
    )

    parser.add_argument(
        "-s",
        "--significance",
        required=True,
        help="Path to the significance annotation matrix TSV file.",
    )

    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="Path to the output image file.",
    )

    parser.add_argument(
        "-t",
        "--title",
        help="Title of the heatmap (default: output filename).",
    )
    
    parser.add_argument(
        "--feature",
        action="store_true",
        help="Flag if the heatmap is for a Per-Feature Score.",
    )

    parser.add_argument(
        "-y",
        "--y_label",
        default="ALT Alleles",
        help="Label for the y-axis (default: %(default)s).",
    )

    parser.add_argument(
        "-x",
        "--x_label",
        default="REF Alleles",
        help="Label for the x-axis (default: %(default)s).",
    )

    return parser.parse_args()


args = parse_args()
print(args)

output_file = Path(args.output_file)
df = pd.read_csv(args.input, sep="\t")

# Get Matrix
matrix_df = df[["ref", "A", "C", "G", "T"]]
matrix_df.set_index("ref", inplace=True)

print(matrix_df.T)

# Load the Significant Boolean Matrix
sig_df = pd.read_csv(args.significance, sep="\t")  # shape must match matrix_df
print(sig_df.T)

# Plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(35, 4))

if args.feature:
    color = "PiYG"
    highlight_color = "black"
    
    max_abs = np.abs(matrix_df.to_numpy()).max()
else:
    color = "Blues"
    highlight_color = "red"

ax = sns.heatmap(
    matrix_df.T,
    cmap=color,
    linewidths=0.2,
    vmin=None if not args.feature else -max_abs,
    vmax=None if not args.feature else max_abs,
    cbar_kws={"pad": 0.01},
)

ax.set(xlabel=None, ylabel=None)
ax.tick_params(axis="y", labelrotation=0)
ax.set_xticklabels(ax.get_xticklabels(), weight="semibold")
ax.set_yticklabels(ax.get_yticklabels(), weight="semibold")

ax.set_xlabel(args.x_label, fontweight="semibold")
ax.set_ylabel(args.y_label, fontweight="semibold")

if args.title:
    title = args.title
    ax.set_title(title, fontweight="semibold")

# --- Highlight significant cells ---
sig_heatmap_df = sig_df.T  # also transposed

for y_idx, row_label in enumerate(sig_heatmap_df.index):  # y = positions
    for x_idx, col_label in enumerate(sig_heatmap_df.columns):  # x = A,C,G,T
        if sig_heatmap_df.loc[row_label, col_label]:  # True -> highlight
            ax.add_patch(
                Rectangle((x_idx, y_idx), 1, 1, fill=False, edgecolor=highlight_color, lw=2.5)
            )

# Save to File
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, bbox_inches="tight", dpi=300)
plt.close()
