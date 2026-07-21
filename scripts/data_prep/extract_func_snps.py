import argparse
import pandas as pd
from pathlib import Path

NON_CODING_FEATURES = [
    "upstream_gene_variant",
    "downstream_gene_variant",
    "intergenic_region"
]

SNP_LIST_COLS = ["chrom", "pos", "annot_id", "id", "ref", "alt", "MAF", "MAF_PCT"]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract a list of SNPs given the h5 file of RiceVarMap."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the h5 file from RiceVarMap.",
    )
    parser.add_argument(
        "--maf_file",
        required=True,
        help="Path to the tsv file containing the MAF extracted from RiceVarMap genotypes.",
    )
    parser.add_argument(
        "--maf",
        type=float,
        default=0.1,
        help="MAF Threshold of SNPs to sample. (Default: 0.1)",
    )
    parser.add_argument(
        "--key",
        required=True,
        help="Key to access the h5 file from RiceVarMap.",
    )
    parser.add_argument(
        "--count",
        required=True,
        type=int,
        help="Number of samples to get.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random State seed.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="tsv file where the output will be saved",
    )
    return parser.parse_args()

args = parse_args()
print(args)

print(f"Reading {args.file}")
df = pd.read_hdf(args.file, args.key)

print(f"Reading MAF file: {args.maf_file}")
maf_df = pd.read_csv(args.maf_file, sep="\t")

maf_df["CHROM"] = maf_df["CHROM"].astype(int)
maf_df = maf_df[["CHROM", "POS", "MAF", "MAF_PCT"]].copy()

# Filter to only contain biallelic snps
biallelic_df = df[
    (df["var_ref"].str.len() == 1) &
    (df["alt"].str.len() == 1) &
    (~df["alt"].str.contains(","))
]

num_snps = len(biallelic_df["var"].unique())
print(f"Number of SNPs: {num_snps}")

# Filter to include only non-coding snps
df_noncoding = biallelic_df[biallelic_df['snpeff_anno'].str.lower().isin(NON_CODING_FEATURES)].copy()

# Form "main columns"
df_noncoding["chrom"] = df_noncoding["var"].str[2:4].astype(int)
df_noncoding["pos"] = df_noncoding["var"].str[4:].astype(int)
df_noncoding.rename(columns={
    "var": "annot_id",
    "var_ref": "ref"
}, inplace=True)
df_noncoding["id"] = "Chr" + df_noncoding["chrom"].astype(str) + ":" + df_noncoding["pos"].astype(str) + "_" + df_noncoding["ref"] + df_noncoding["alt"]

# Merge MAF
print("Merging MAF file")
df_noncoding = df_noncoding.merge(
    maf_df,
    left_on=["chrom", "pos"],
    right_on=["CHROM", "POS"],
    how="left"
)
df_noncoding.drop(columns=["CHROM", "POS"], inplace=True)

# Keep only SNPs with MAF > 0.1
df_noncoding = df_noncoding[
    df_noncoding["MAF"] > args.maf
].copy()
num_snps = len(df_noncoding["id"].unique())
print(f"Number of Non-coding SNPs with MAF > {args.maf}: {num_snps}")

# Drop Redudant Ids
df_noncoding = df_noncoding.drop_duplicates(subset="id").reset_index(drop=True)
df_noncoding = df_noncoding.drop_duplicates(subset="pos").reset_index(drop=True)
num_snps = len(df_noncoding["id"].unique())
print(f"Final Set of Non-coding SNPs: {num_snps}")

# Sample
print(f"Sampling: {args.count}")
final = df_noncoding.sample(n=args.count, random_state=args.seed)
final = final.sort_values(by="pos").reset_index(drop=True)

output_f = Path(args.output)
output_f.parent.mkdir(parents=True, exist_ok=True)

final.to_csv(
    output_f,
    columns=SNP_LIST_COLS,
    sep="\t",
    index=False
)
print(f"Saved results to {output_f}")

