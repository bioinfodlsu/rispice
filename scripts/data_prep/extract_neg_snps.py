import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm
from pathlib import Path 

SNP_LIST_COLS = ["chrom", "pos", "annot_id", "id", "ref", "alt"]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract a list of SNPs given the h5 file of RiceVarMap."
    )
    parser.add_argument(
        "-i",
        "--input_file",
        required=True,
        help="Path to the Positive SNPs.",
    )
    parser.add_argument(
        "--rice_snps",
        required=True,
        help="Path to the 3KRG SNPs where the negative samples will be sampled.",
    )
    parser.add_argument(
        "--gene_file",
        required=True,
        help="Path to the genes file.",
    )
    parser.add_argument(
        "--func_snps_file",
        required=True,
        help="Path to the h5 file from RiceVarMap.",
    )
    parser.add_argument(
        "--func_snps_key",
        required=True,
        help="Key to access the h5 file from RiceVarMap.",
    )
    parser.add_argument(
        "--count",
        required=True,
        type=int,
        help="Number of samples to sample per positive SNP.",
    )
    parser.add_argument(
        "--max_dist",
        required=True,
        type=int,
        help="How far from the positive SNP you could sample the negative SNP from (in bp).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random State seed.",
    )
    parser.add_argument(
        "--maf_tol",
        type=float,
        default=0.05,
        help="Tolerance for MAF.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="tsv file where the output will be saved",
    )
    return parser.parse_args()

def is_coding(pos, intervals):
    """
    Returns True if position overlaps a gene interval.
    """
    return np.any((intervals[:, 0] <= pos) & (pos <= intervals[:, 1]))

args = parse_args()
print(args)

print("[Loading Data]")
print(f"Reading Functional SNPs: {args.func_snps_file}")
func_snps = pd.read_hdf(args.func_snps_file, args.func_snps_key)
func_snps["pos"] = func_snps["var"].str[4:].astype(int)
print(f"{len(func_snps)} snps from ricevarmap")

print(f"Reading Genes: {args.gene_file}")
genes_df = pd.read_csv(args.gene_file, sep="\t")
genes_df = genes_df[(genes_df["chrom"] == args.func_snps_key)] #chr06 formatting
print(f"{len(genes_df)} genes")

print(f"Reading 3KRG: {args.rice_snps}")
rg_3k_df = pd.read_csv(
    args.rice_snps,
    sep="\t",
    comment="#",
    header=None,
    names=["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO"]
)

# Only consider biallelic
rg_3k_df = rg_3k_df[
    (rg_3k_df["REF"].str.len() == 1) &
    (rg_3k_df["ALT"].str.len() == 1) &
    (~rg_3k_df["ALT"].str.contains(","))
]
print(f"{len(rg_3k_df)} snps from the 3KRG")

print(f"Reading Postive Samples: {args.input_file}")
positives_df = pd.read_csv(args.input_file, sep="\t")
print(f"{len(positives_df)} positive samples")

# PREP LOOKUPs
print("[Prepping Lookups]")
# Functional SNP positions
func_positions = set(func_snps["pos"].astype(int))
gene_intervals = genes_df[["start", "end"]].to_numpy()
rg_3k_df["POS"] = rg_3k_df["POS"].astype(int)

# Remove known functional SNPs first
rg_3k_df = rg_3k_df[
    ~rg_3k_df["POS"].isin(func_positions)
].copy()

print(f"{len(rg_3k_df)} SNPs after removing functional SNPs and coding SNPs")

# Precompute MAF
rg_3k_df["AF"] = rg_3k_df["INFO"].str.extract(r"AF[:=]([0-9.]+)").astype(float)
rg_3k_df["MAF"] = rg_3k_df["AF"].apply(lambda af: min(af, 1 - af))
rg_3k_df["MAF_PCT"] = rg_3k_df["MAF"].rank(pct=True)

# --------------------------------------------------
# Sample matched negatives
# --------------------------------------------------

negative_samples = []
used_positions = set() # prevent reusing same SNP

for _, row in tqdm(positives_df.iterrows(), total=len(positives_df)):
    pos = int(row["pos"])
    pos_maf = float(row["MAF"])
    pos_pct = row["MAF_PCT"]

    # Candidate window
    lower = pos - args.max_dist
    upper = pos + args.max_dist

    candidates = rg_3k_df[
        (rg_3k_df["POS"] >= lower) &
        (rg_3k_df["POS"] <= upper)
    ]
    
    if candidates.empty:
        continue

    # ---- remove coding SNPs ----
    candidates = candidates[
        ~candidates["POS"].apply(
            lambda x: is_coding(x, gene_intervals)
        )
    ]
    
    if candidates.empty:
        continue

    # ---- remove already used ----
    candidates = candidates[
        ~candidates["POS"].isin(used_positions)
    ]
    
    if candidates.empty:
        continue
    
    # ---- MAF MATCHING FILTER ----
    # candidates = candidates[
    #     (candidates["MAF"] >= pos_maf - args.maf_tol) &
    #     (candidates["MAF"] <= pos_maf + args.maf_tol)
    # ]
    candidates = candidates[
        (candidates["MAF_PCT"] >= pos_pct - args.maf_tol) &
        (candidates["MAF_PCT"] <= pos_pct + args.maf_tol)
    ]

    if candidates.empty:
        continue

    n = min(args.count, len(candidates))
    
    sampled = candidates.sample(n=n, random_state=args.seed)
    negative_samples.append(sampled)
    
    used_positions.update(sampled["POS"].tolist())

negative_df = pd.concat(negative_samples, ignore_index=True)

print(f"Generated {len(negative_df)} negative samples")

# Save
output_f = Path(args.output)
output_f.parent.mkdir(parents=True, exist_ok=True)

negative_df.to_csv(
    output_f,
    sep="\t",
    index=False
)
print(f"Saved results to {output_f}")