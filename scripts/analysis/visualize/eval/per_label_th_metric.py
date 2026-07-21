import argparse
import pandas as pd
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a Bar Graph comparing a Metric Per Label."
    )
    parser.add_argument(
        "-i",
        "--input_file",
        required=True,
        help=".tsv file containing the dataframe to be processed.",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="The visualized graph location.",
    )
    parser.add_argument(
        "-m",
        "--metric",
        required=True,
        help="A column within the dataframe.",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="The title of the graph. (Default: *output_filename*)",
    )
    parser.add_argument(
        "--sort_desc",
        action="store_true",
        help="Whether to sort the graph in descending order",
    )
    parser.add_argument(
        "--x_key",
        default="mark",
        help="key to be used when accessing the data in the df for the x-axis.",
    )
    parser.add_argument(
        "--x_label",
        default="Histone Mark",
        help="Label displayed in the graph for the x-axis.",
    )
    parser.add_argument(
        "--y_label",
        help="Label displayed in the graph for the y-axis.",
    )
    parser.add_argument(
        "--dont_limit",
        action="store_true",
        help="Don't set a static limit.",
    )
    parser.add_argument(
        "--percent",
        action="store_true",
        help="Convert 0 to 1 to percentage (0 to 100).",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

output_file = Path(args.output_file)

df = pd.read_csv(args.input_file, sep="\t")

if args.sort_desc:
    df = df.sort_values(by=args.metric, ascending=False)

if args.percent:
    df[args.metric] = df[args.metric] * 100

print(df[[args.x_key, args.metric]])

# Plot
print(f"Plotting the data...")
sns.set_theme(style="whitegrid", font="Open Sans")
plt.figure(figsize=(12, 6))

ax = sns.barplot(
    data=df,
    x=args.x_key,
    y=args.metric
)

ax.bar_label(
    ax.containers[0],
    fontsize=11, 
    fmt='%.1f%%' if args.percent else '%.3f',
    fontweight='semibold', 
    padding=3
);

if not args.dont_limit:
    ceiling = 100 if args.percent else 1
    ax.set_ylim(0, ceiling)

x_label = args.x_label
y_label = args.y_label if args.y_label else args.metric

ax.set_xlabel(x_label, fontweight="semibold")
ax.set_ylabel(y_label, fontweight="semibold")
if args.percent:
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100))

title = args.title if args.title else output_file.stem
ax.set_title(title, fontweight="semibold")

# Save to file
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()