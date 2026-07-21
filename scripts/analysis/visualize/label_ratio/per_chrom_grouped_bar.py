import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
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
        required=True,
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
    return parser.parse_args()


args = parse_args()
print(args)

chrom_file = Path(args.chrom_file)
print(f"Reading File: {chrom_file}")
data = pd.read_csv(chrom_file)
chrom = chrom_file.stem

print(f"Reading Column File {args.column_file}")
marks = pd.read_csv(args.column_file)

# Form the dataset for the stacked bar plot
print(f"Forming the dataset...")
df = pd.concat([marks, data], axis=1)
print(df)

df_long = df.melt(
    id_vars=args.column_name, value_vars=["1", "0"], var_name="label", value_name="count"
)

# make label readable (optional)
df_long["label"] = df_long["label"].astype(str)
df_long["label"] = df_long["label"].map({"1": "Positive (1)", "0": "Negative (0)"})

sns.set_theme(style="whitegrid", font="Open Sans")
fig, ax = plt.subplots(figsize=(12, 6))

sns.barplot(
    data=df_long,
    x=args.column_name,
    y="count",
    hue="label",
    hue_order=["Positive (1)", "Negative (0)"],
    palette={"Positive (1)": "#4C72B0", "Negative (0)": "#DD8452"},
    ax=ax,
)

for container in ax.containers:
    ax.bar_label(
        container,
        labels=[f"{v/1_000:.0f}K" for v in container.datavalues],
        fontsize=9,
        padding=2,
        fontweight="semibold",
    )

ax.set_yticks([0, 100000, 200000, 300000, 400000])
ax.yaxis.set_major_formatter(
    mtick.FuncFormatter(lambda x, _: "0" if x == 0 else f"{int(x/1_000)}K")
)

ax.set_xlabel("Chromatin Feature", fontsize=13, fontweight="semibold")
ax.set_ylabel("Sample Count (K)", fontsize=12, fontweight="semibold")

ax.tick_params(
    axis="x",
    labelsize=10,
    which="major",
    bottom=True,
    length=4, 
    width=1,
    direction="out",
    labelrotation=45
)
ax.tick_params(axis="y", labelsize=12)

ax.set_title(
    f"Positive and Negative Sample Counts Per Chromatin Feature (Chr{chrom})",
    fontweight="semibold",
)
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

# Save to output file
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / f"{chrom}.png"
print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
