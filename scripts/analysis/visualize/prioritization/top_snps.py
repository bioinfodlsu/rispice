import argparse
import pandas as pd
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a VCF file to a SNP List for processing."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the top_variants file.",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="Path to the desired output file.",
    )
    parser.add_argument(
        "--x_key",
        default="id",
        help="key to be used when accessing the data in the df for the x-axis.",
    )
    parser.add_argument(
        "-m",
        "--metric",
        default="Variant",
        help="A column within the dataframe.",
    )
    
    parser.add_argument(
        "--x_label",
        default="SNPs",
        help="Label displayed in the graph for the x-axis.",
    )
    parser.add_argument(
        "--y_label",
        default="Variant Score",
        help="Label displayed in the graph for the y-axis.",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="The title of the graph. (Default: *output_filename*)",
    )
    parser.add_argument(
        "--width",
        default=6,
        type=int,
        help="Width of the graph. (Recommended: 20var=6w, 100var=20w)",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

output_file = Path(args.output_file)
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

title = args.title if args.title else output_file.stem
ax.set_title(title, fontweight="semibold")

ax.tick_params(axis='x', labelrotation=90)

# Save to file
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()