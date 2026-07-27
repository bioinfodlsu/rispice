import argparse, pandas as pd
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.analysis.visualize.prioritization.per_feature_scores",
        description="Generate a heatmap of per-feature scores for prioritized variants."
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the per_feature_scores.tsv file.",
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
        help="Plot title. (Default: output filename)",
    )
    parser.add_argument(
        "-y",
        "--y_label",
        default="SNP",
        help="Label for the y-axis. (Default: SNP)",
    )
    parser.add_argument(
        "-x",
        "--x_label",
        default="Chromatin Features",
        help="Label for the x-axis. (Default: Chromatin Features)",
    )
    parser.add_argument(
        "--ratio_label",
        default="Difference in Log-Odds",
        help="Label for the color bar. (Default: Difference in Log-Odds)",
    )
    parser.add_argument(
        "--width",
        default=15,
        type=int,
        help="Plot width in inches. (Default: 15)",
    )
    parser.add_argument(
        "--height",
        default=12,
        type=int,
        help="Plot height in inches. (Default: 12; recommended for 20 SNPs)",
    )
    parser.add_argument(
        "--threshold_dir",
        help="Directory containing per-feature significance threshold files.",
    )
    parser.add_argument(
        "--significance_lvl",
        default=0.05,
        type=float,
        help="Significance level used to annotate significant scores. (Default: 0.05)",
    )

    return parser.parse_args()

args = parse_args()
print(args)

output_file = Path(args.output_file)
df = pd.read_csv(args.input, sep="\t")
df.set_index("id", inplace=True)

# Sort the columns based on impact
impact_scores = df.abs().mean(axis=0)
sorted_columns = impact_scores.sort_values(ascending=False).index

df = df[sorted_columns]
print(df)

# Load the thresholds
thresholds = {}
if args.threshold_dir:
    threshold_dir = Path(args.threshold_dir)

    for feature in df.columns:
        threshold_file = threshold_dir / f"{feature}.tsv"

        threshold_df = pd.read_csv(threshold_file, sep="\t")

        row = threshold_df[
            (threshold_df["significance_lvl"] == args.significance_lvl)
        ]

        if len(row) != 1:
            raise ValueError(
                f"Expected exactly one threshold for "
                f"{feature} at significance level "
                f"{args.significance_lvl}"
            )

        thresholds[feature] = float(row.iloc[0]["score"])

# Calculate the absolute maximum value in the dataframe to force a symmetric color bar
max_val = df.abs().max().max()

# Plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(args.width, args.height))

ax = sns.heatmap(
    df, 
    cmap="PiYG",       # Red-to-Blue (Red = Increase Prob of Histone Marks, Blue = Decrease Prob of Histone Marks)
    center=0,            # Forces 0 (no change) to be white 
    vmin=-max_val,       # Force the absolute negative minimum
    vmax=max_val,        # Force the absolute positive maximum
    annot=True,          # Shows the actual LFC values in the cells
    fmt=".2f",           # Limits to 2 decimal places
    linewidths=.5,       # Adds thin lines between cells for clarity
    cbar_kws={"label": args.ratio_label},
    annot_kws={"weight": "semibold"}
)


# Add significance
if args.threshold_dir:
    for row_idx, snp in enumerate(df.index):
        for col_idx, feature in enumerate(df.columns):

            score = df.loc[snp, feature]
            threshold = thresholds[feature]

            # significance based on absolute effect size
            if abs(score) >= threshold:

                edge_color = "white" if abs(score) >= 0.20 else "black"
                
                rect = Rectangle(
                    (col_idx + 0.05, row_idx + 0.05),
                    0.90,
                    0.90,
                    fill=False,
                    edgecolor=edge_color,
                    linewidth=2,
                    linestyle=":",
                    clip_on=False,
                    zorder=10
                )

                ax.add_patch(rect)

ax.set(xlabel=None, ylabel=None)
ax.tick_params(axis='x', labelrotation=90)
ax.set_xticklabels(ax.get_xticklabels(), weight="semibold")
ax.set_yticklabels(ax.get_yticklabels(), weight="semibold")

ax.set_xlabel(args.x_label, fontweight="semibold")
ax.set_ylabel(args.y_label, fontweight="semibold")

title = args.title if args.title else output_file.stem
ax.set_title(title, fontweight="semibold")

print(f"Saving results to {output_file}")
plt.tight_layout()

# makedir
output_file.parent.mkdir(parents=True, exist_ok=True)

plt.savefig(output_file, dpi=300, bbox_inches="tight", pad_inches=0.2)
plt.close()