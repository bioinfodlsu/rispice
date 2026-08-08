import argparse
import pandas as pd
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.analysis.visualize.prioritization.top_variants",
        description="Generate a plot from a RiSPICE top_variants.tsv file."
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input top_variants.tsv file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output image file.",
    )
    parser.add_argument(
        "--x_key",
        default="id",
        help="Column to use for the x-axis. (Default: id)",
    )
    parser.add_argument(
        "-m",
        "--metric",
        default="Variant",
        help="Column to plot on the y-axis. (Default: Variant)",
    )
    parser.add_argument(
        "--x_label",
        default="SNPs",
        help="Label for the x-axis. (Default: SNPs)",
    )
    parser.add_argument(
        "--y_label",
        default="Overall Score",
        help="Label for the y-axis. (Default: Overall Score)",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="Plot title. (Default: output filename)",
    )
    parser.add_argument(
        "--width",
        default=6,
        type=int,
        help="Plot width in inches. (Recommended: 6 for ~20 variants, 20 for ~100 variants)",
    )

    return parser.parse_args()

args = parse_args()
print(args)

output_file = Path(args.output)
df = pd.read_csv(args.input, sep="\t")
print(df)

# Plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(args.width, 6))

ax = sns.barplot(
    data=df,
    x=args.x_key,
    y=args.metric
)

x_label = args.x_label
y_label = args.y_label if args.y_label else args.metric

ax.set_xlabel(x_label, fontweight="semibold")
ax.set_ylabel(y_label, fontweight="semibold")

if args.title:
    title = args.title
    ax.set_title(title, fontweight="semibold")

ax.tick_params(axis='x', labelrotation=90)

# Save to file
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()