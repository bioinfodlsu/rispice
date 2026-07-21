import argparse
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a stacked bar plot given the Histone Mark file."
    )
    parser.add_argument(
        "-f",
        "--mark_file",
        required=True,
        help="The file to be visualized.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="The location where the output files would be saved.",
    )
    parser.add_argument(
        "--graph_title",
        help="Custom title for the graph output.",
    )
    parser.add_argument(
        "--output_fn",
        help="Filename of the output file.",
    )
    return parser.parse_args()

args = parse_args()
print(args)

mark_file = Path(args.mark_file)
print(f"Reading File: {mark_file}")
df = pd.read_csv(mark_file)
histone_mark = mark_file.stem

# Compute pct values
print(f"Forming the dataset...")
df["ones_pct"] = df["ratio"] * 100
df["zeros_pct"] = 100 - df["ones_pct"]          # Get pct of zeros
print(df)

# Visualize
# Plot the Dataframe
print(f"Plotting the data...")

sns.set_theme(style="whitegrid", context="talk", font="Open Sans")
palette = sns.color_palette("mako", 2)

fig, ax = plt.subplots(figsize=(12, 6))

# bottom layer: 1s
sns.barplot(
    data=df,
    y="chromosome",
    x="ones_pct",
    color=palette[1],
    ax=ax,
    label="Positive (1)"
)

# top layer: 0s (stacked)
sns.barplot(
    data=df,
    y="chromosome",
    x="zeros_pct",
    left=df["ones_pct"],
    color=palette[0],
    ax=ax,
    label="Negative (0)"
)

# Specify the title
if args.graph_title is None:
    graph_title = f"Prevalence per Chromosome ({histone_mark})"
else:
    graph_title = args.graph_title

ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100"])
ax.set_xlabel("Prevalence", fontsize=13, fontweight="semibold")
ax.set_ylabel("Chromosome", fontsize=12, fontweight="semibold")
ax.set_title(graph_title, fontweight="semibold")  # edit chr
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc="upper right")

ax.tick_params(axis="x", labelsize=14)
ax.tick_params(axis="y", labelsize=14)

sns.despine(left=True, bottom=True)

for i, pct in enumerate(df["ones_pct"]):
    ax.text(pct / 2, i, f"{pct:.1f}%", va="center", ha="center", fontsize=10)
    
# Save to output file
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

if args.output_fn is None:
    f_name = histone_mark
else:
    f_name = args.output_fn

output_file = output_dir / f"{f_name}.png"
print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()