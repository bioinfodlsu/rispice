import argparse
import numpy as np
from pathlib import Path
from ....utils import SampleUtils

import seaborn as sns
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a `bigWig` chromatin feature track (ATAC-seq, ChIP-seq, etc.)."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Chromatin Profile.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="The output file for the figure.",
    )
    parser.add_argument(
        "--chrom",
        required=True,
        type=int,
        help="Chromosome Number.",
    )
    parser.add_argument(
        "--start",
        required=True,
        type=int,
        help="Start bp.",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=int,
        help="End bp.",
    )
    parser.add_argument(
        "--chrom_feature",
        help="Specify Chromatin Feature in the title.",
    )
    parser.add_argument(
        "--color",
        default="steelblue",
        help="Specify the color.",
    )
    parser.add_argument(
        "--smooth",
        type=int,
        help="Smoothen the peaks.",
    )
    return parser.parse_args()


args = parse_args()
print(args)

values = SampleUtils.getValues(
    args.input,
    f"chr{args.chrom}",
    args.start,
    args.end
)
values = np.nan_to_num(values)
values = np.log1p(values)
if args.smooth:
    values = gaussian_filter1d(values, args.smooth)  

positions = np.arange(args.start, args.end)

print(f"Plotting the data...")
sns.set_theme(style="white", font="Open Sans")
plt.figure(figsize=(16, 4))

ax = plt.gca()

ax.fill_between(positions, values, alpha=0.8, color=args.color)
ax.set_xlim(args.start, args.end)
ax.set_ylim(bottom=0)
ax.set_xlabel(f"Genomic position (Chr{args.chrom})", fontweight="semibold")
ax.set_ylabel("log1p(signal)", fontweight="semibold")

title = f"Chr{args.chrom}:{args.start:,}-{args.end:,}"
if args.chrom_feature:
    title = f"{args.chrom_feature} ({title})"

ax.set_title(title, fontweight="semibold")

ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.spines[["top", "right"]].set_visible(False)

# Save to File
output_file = Path(args.output)
output_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {output_file}")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
