import argparse
import pandas as pd
from pathlib import Path

import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a matrix containing models as columns and labels as rows."
    )
    parser.add_argument(
        "-f",
        "--matrix_file",
        required=True,
        help="Directory containing all the label ratio files to be aggregated.",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="The location where the output files would be saved.",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="The title of the graph. (Default: *output_filename*)",
    )
    parser.add_argument(
        "-y",
        "--y_label",
        default="Histone mark",
        help="Set the y label for the graph.",
    )
    parser.add_argument(
        "-x",
        "--x_label",
        default="Model",
        help="Set the x label for the graph.",
    )
    parser.add_argument(
        "-r",
        "--ratio_label",
        help="Set the label of the Ratio",
    )
    return parser.parse_args()

args = parse_args()
print(args)

output_file = Path(args.output_file)
df = pd.read_csv(args.matrix_file, sep="\t", index_col=0)
print(df)

# plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(12, 6))
ratio_label = args.ratio_label if args.ratio_label else output_file.stem.upper()
ax = sns.heatmap(
    df,
    cmap="crest",
    vmin=0,
    vmax=1,
    linewidths=0.2,
    linecolor="white",
    cbar_kws={"label": ratio_label},
    annot=True, 
    fmt=".3f", 
    annot_kws={"weight": "bold"}
)

ax.set_xlabel(args.x_label, fontweight="semibold")
ax.set_ylabel(args.y_label, fontweight="semibold")

title = args.title if args.title else output_file.stem
ax.set_title(title, fontweight="semibold")

# Set
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
