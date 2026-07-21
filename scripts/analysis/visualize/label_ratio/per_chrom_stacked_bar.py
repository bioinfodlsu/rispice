import argparse
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a stacked bar plot given the chromosome file."
    )
    parser.add_argument(
        "-f",
        "--chrom_file",
        required=True,
        help="The file to be visualized.",
    )
    parser.add_argument(
        "-c",
        "--column_file",
        help="A csv file containing all of the columns to get the ratio of.",
    )
    parser.add_argument(
        "--column_name",
        default="features",
        help="The column name of the column file.",
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
    return parser.parse_args()

args = parse_args()
print(args)

chrom_file = Path(args.chrom_file)
print(f"Reading File: {chrom_file}")
data = pd.read_csv(chrom_file)
chrom = chrom_file.stem

if not args.column_name in data.columns:
    print(f"Reading Column File {args.column_file}")
    marks = pd.read_csv(args.column_file)

    # Form the dataset for the stacked bar plot
    print(f"Forming the dataset...")
    df = pd.concat([marks, data], axis=1)
else:
    df = data

df["ones_pct"] = df["ratio"] * 100
df["zeros_pct"] = 100 - df["ones_pct"]          # Get pct of zeros
df = df.sort_values("ratio", ascending=False)   # Sort desc
print(df)

# Plot the Dataframe
print(f"Plotting the data...")

sns.set_theme(style="whitegrid", context="talk", font="Open Sans")
palette = sns.color_palette("mako", 2)

fig, ax = plt.subplots(figsize=(12, 6))

# bottom layer: 1s
sns.barplot(
    data=df,
    y=args.column_name,
    x="ones_pct",
    color=palette[1],
    ax=ax,
    label="Positive (1)"
)

# top layer: 0s (stacked)
sns.barplot(
    data=df,
    y=args.column_name,
    x="zeros_pct",
    left=df["ones_pct"],
    color=palette[0],
    ax=ax,
    label="Negative (0)"
)

# Specify the title
if args.graph_title is None:
    graph_title = f"Prevalence per Chromatin Feature (Chr{chrom})"
else:
    graph_title = args.graph_title

ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100"])
ax.set_xlabel("Prevalence", fontsize=13, fontweight="semibold")
ax.set_ylabel("Chromatin Feature", fontsize=12, fontweight="semibold")
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

output_file = output_dir / f"{chrom}.png"
print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
