import argparse
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check all files (label ratios) and generate a matrix of label ratios (across all chromosomes)."
    )
    parser.add_argument(
        "-f",
        "--matrix_file",
        required=True,
        help="Directory containing all the label ratio files to be aggregated.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="The location where the output files would be saved.",
    )
    parser.add_argument(
        "--title",
        default="Prevalence Across the Nipponbare Genome",
        help="Set the title for the graph."
    )
    return parser.parse_args()


args = parse_args()
print(args)

print(f"Reading Matrix File: {args.matrix_file}")
df = pd.read_csv(args.matrix_file, index_col=0)

# Sort by the mean (descending, highest first)
print(f"Sorting data by the average per mark...")
df["mean"] = df.mean(axis=1)
df.sort_values("mean", ascending=False, inplace=True)
df.drop(columns="mean", inplace=True)
print(df)

vmin = np.percentile(df.values, 5)
vmax = np.percentile(df.values, 95)

# plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(12, 6))
ax = sns.heatmap(
    df,
    cmap="mako",
    vmin=vmin,
    vmax=vmax,
    linewidths=0.2,
    linecolor="white",
    cbar_kws={"label": "Ratio"},
)

ax.set_xlabel("Chromosome", fontweight="semibold")
ax.set_ylabel("Chromatin Feature", fontweight="semibold")
ax.set_title(args.title, fontweight="semibold")

# Set
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / f"genome_wide_prevalence.png"
print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
