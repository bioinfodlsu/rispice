import argparse
import numpy as np
import pyBigWig
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a `bigWig` chromatin feature track (ATAC-seq, ChIP-seq, etc.) Chromosome-wide."
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
        default=3,
        type=int,
        help="Smoothen the peaks.",
    )
    parser.add_argument(
        "--n_bins",
        default=5000,
        type=int,
        help="bins.",
    )
    parser.add_argument(
        "--line_width",
        default=0.8,
        type=int,
        help="line-width.",
    )
    return parser.parse_args()

def get_values(path, chrom, n_bins):
    bw = pyBigWig.open(path)
    chrom_len = bw.chroms(chrom)  # get chromosome length
    
    # fetch mean signal in n_bins bins instead of per-base
    values = np.array(bw.stats(chrom, 0, chrom_len, type="mean", nBins=n_bins))
    bw.close()
    
    return values, chrom_len
    
args = parse_args()
print(args)

values, chrom_len = get_values(
    args.input,
    f"chr{args.chrom}",
    args.n_bins
)

values = np.nan_to_num(values)
smoothed = gaussian_filter1d(np.log1p(values), sigma=args.smooth)
positions = np.linspace(0, chrom_len, args.n_bins)

print(f"Plotting the data...")
sns.set_theme(style="white", font="Open Sans")
plt.figure(figsize=(16, 4))

ax = plt.gca()

ax.fill_between(positions, smoothed, alpha=0.7, color=args.color)
ax.plot(positions, smoothed, alpha=1.0, color=args.color, linewidth=args.line_width)
ax.set_xlim(0, chrom_len)
ax.set_ylim(bottom=0)
ax.set_xlabel(f"Genomic position (Chr{args.chrom})", fontweight="semibold")
ax.set_ylabel("log1p(signal)", fontweight="semibold")

title = f"Chr{args.chrom}"
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