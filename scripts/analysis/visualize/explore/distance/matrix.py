import argparse, pandas as pd, numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a the distance matrix via a heatmap."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="tsv files containing the matrix.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Save results to a png file.",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="Set the title for the graph."
    )
    parser.add_argument(
        "--cbar_label",
        required=True,
        help="Set the label for the cbar."
    )
    parser.add_argument(
        "--log",
        action="store_true",
    )
    return parser.parse_args()

# Function to format numbers as K/M
def human_format(x):
    if x >= 1e6:
        return f"{x/1e6:.1f}M"
    elif x >= 1e3:
        return f"{x/1e3:.1f}K"
    else:
        return str(int(x))

args = parse_args()
print(args)

df = pd.read_csv(args.input, sep="\t", index_col="feature")

plot_df = df.copy()
if args.log:
    plot_df = np.log1p(plot_df)

g = sns.clustermap(plot_df, method="ward", metric="euclidean")

row_order = g.dendrogram_row.reordered_ind
col_order = g.dendrogram_col.reordered_ind

plt.close(g.figure)

ordered = df.iloc[row_order, col_order]
annot = df.applymap(human_format)
annot_ordered = annot.iloc[row_order, col_order]

sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(14, 9))
ax = sns.heatmap(
    ordered,
    cmap="mako_r",
    annot=annot_ordered,
    annot_kws={"weight": "semibold", "size": 11},
    fmt="",
    linewidths=0.2,
    linecolor="white",
    cbar_kws={"label": args.cbar_label},
)

ax.set_xlabel("Histone mark", fontweight="semibold", labelpad=20)
ax.set_ylabel("Histone mark", fontweight="semibold", labelpad=20)

if args.title:
    ax.set_title(args.title, fontweight="semibold")

# Save
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(output, dpi=300)
plt.close()
print(f"Saved results to {output}")