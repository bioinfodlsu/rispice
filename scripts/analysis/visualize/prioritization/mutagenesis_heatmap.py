import argparse
import pandas as pd
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate the Heatmap for the Mutagenesis Analysis."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the mutagenesis dataframe file.",
    )
    parser.add_argument(
        "-s",
        "--sig_matrix",
        required=True,
        help="Path to the significant matrix file.",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="Path to the desired output file.",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="The title of the graph. (Default: *output_filename*)",
    )
    parser.add_argument(
        "-y",
        "--y_label",
        default="ALT Alleles",
        help="Set the y label for the graph.",
    )
    parser.add_argument(
        "-x",
        "--x_label",
        default="REF Alleles",
        help="Set the x label for the graph.",
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
sig_df = pd.read_csv(args.sig_matrix, sep="\t")  # shape must match matrix_df
print(sig_df.T)

# Plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(35, 4))

ax = sns.heatmap(matrix_df.T, cmap="Blues", linewidths=0.2)

ax.set(xlabel=None, ylabel=None)
ax.tick_params(axis="y", labelrotation=0)
ax.set_xticklabels(ax.get_xticklabels(), weight="semibold")
ax.set_yticklabels(ax.get_yticklabels(), weight="semibold")

ax.set_xlabel(args.x_label, fontweight="semibold")
ax.set_ylabel(args.y_label, fontweight="semibold")

title = args.title if args.title else output_file.stem
ax.set_title(title, fontweight="semibold")

# --- Highlight significant cells ---
sig_heatmap_df = sig_df.T  # also transposed

for y_idx, row_label in enumerate(sig_heatmap_df.index):  # y = positions
    for x_idx, col_label in enumerate(sig_heatmap_df.columns):  # x = A,C,G,T
        if sig_heatmap_df.loc[row_label, col_label]:  # True -> highlight
            ax.add_patch(
                Rectangle((x_idx, y_idx), 1, 1, fill=False, edgecolor="red", lw=2.5)
            )

# Save to File
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
