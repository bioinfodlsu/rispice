import argparse
import pandas as pd
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Max Effect Graph for Mutagenesis Analysis."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the mutagenesis dataframe file.",
    )
    parser.add_argument(
        "-t",
        "--thresholds",
        required=True,
        help="Computed genome-wide thresholds",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="Path to the desired output file.",
    )
    parser.add_argument(
        "--title",
        help="The title of the graph. (Default: *output_filename*)",
    )
    parser.add_argument(
        "-y",
        "--y_label",
        default="Max Variant Effect Score",
        help="Set the y label for the graph.",
    )
    parser.add_argument(
        "-x",
        "--x_label",
        default="REF Alleles",
        help="Set the x label for the graph.",
    )
    parser.add_argument(
        "-s",
        "--significance",
        default=0.1,
        type=float,
        help="Genome-wide Significance Level to use. (default: 0.1)"
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

output_file = Path(args.output_file)
df = pd.read_csv(args.input, sep="\t")
print(df)

threshold_df = pd.read_csv(args.thresholds, sep="\t")
threshold = threshold_df[threshold_df["significance_lvl"] == args.significance].to_dict(orient='records')[0]
sig_line = threshold["score"]
print("significance threshold ({0}): {1}".format(args.significance, sig_line))

# plot
print(f"Plotting the data...")
sns.set_theme(style="white", font="Open Sans")
plt.figure(figsize=(25, 4))

ax = sns.lineplot(data=df, x="id", y="max_effect", marker="o")

# Replace x-axis ticks with ref alleles
plt.xticks(ticks=range(len(df)), labels=df["ref"])
ax.tick_params(axis='x', labelrotation=0)
ax.set_xticklabels(ax.get_xticklabels(), weight='semibold')

# Add significance line if there are significant points
if sig_line is not None:
    ax.axhline(y=sig_line, color="red", linestyle="--", linewidth=2)
    ax.legend(fontsize=12)

ax.set_xlabel(args.x_label, fontweight="semibold")
ax.set_ylabel(args.y_label, fontweight="semibold")

title = args.title if args.title else output_file.stem
ax.set_title(title, fontweight="semibold")

# Save to file
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.margins(x=0)  # Removes left/right margin
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()