import argparse, pandas as pd, numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a co-occurrence matrix via a clustermap."
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Dataset (or parquet file) containing all the labels.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Save results to a png file.",
    )
    parser.add_argument(
        "--title",
        help="Set the title for the graph."
    )
    parser.add_argument(
        "--log",
        action="store_true",
    )
    parser.add_argument(
        "--norm",
        action="store_true",
    )
    parser.add_argument(
        "--metric",
        default="euclidean",
        help="refer to seaborn.clustermap (notable options: euclidean, correlation)"
    )
    parser.add_argument(
        "--method",
        default="ward",
        help="refer to seaborn.clustermap (notable options: ward, single)"
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

df = pd.read_csv(args.input, sep="\t", index_col="Feature")
print(df)

cbar_label = "Label Co-occurrence"
# Transform data for coloring
plot_df = df.copy()

if args.log:
    plot_df = np.log1p(plot_df)
    cbar_label += " (log scaled)"
if args.norm:
    plot_df = plot_df.div(plot_df.sum(axis=1), axis=0)
    cbar_label += " (normalized)"

# Create annotations from raw counts (or from transformed if desired)
annot = df.applymap(human_format)  # raw counts

# plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
g = sns.clustermap(
    plot_df,
    cmap="viridis",
    linewidths=0.2,
    linecolor="white",
    annot=annot,           # Your custom K/M string matrix
    fmt="",                # Since 'annot' is already strings
    annot_kws={"weight": "semibold", "size": 11},
    dendrogram_ratio=0.1, # Size of the trees on the side/top
    colors_ratio=0.03,
    figsize=(14, 9),      # Clustermaps usually need more vertical space
    method=args.method,         # Linkage method for grouping
    metric=args.metric,    # Distance metric
    cbar_pos=None
)

g.ax_heatmap.set_xlabel("Histone mark", fontweight="semibold", labelpad=20)
g.ax_heatmap.xaxis.tick_bottom()
g.ax_heatmap.set_ylabel("Histone mark", fontweight="semibold", labelpad=20)

# title = args.title if args.title else Path(args.input).stem
# g.figure.suptitle(title, fontweight="semibold")

# Set
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output}")
plt.tight_layout()
plt.savefig(output, dpi=300)
plt.close()