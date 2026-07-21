import argparse
import pandas as pd
from tqdm import tqdm
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a MAF df given freq."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the generated .freq file from vcftools.",
    )
    parser.add_argument(
        "--chrom",
        required=True,
        type=int,
        help="Chromosome number.",
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

# Read the file
rows = []
with open(args.file) as f:
    header = f.readline().strip().split("\t")

    for line in tqdm(f, desc="Processing variants"):
        parts = line.strip().split("\t")

        chrom = parts[0]
        pos = int(parts[1])
        n_alleles = int(parts[2])
        n_chr = int(parts[3])

        # Remaining columns are allele:freq
        allele_freqs = parts[4:]

        freqs = []

        freqs = [float(v.split(":")[1]) for v in allele_freqs]
        max_af = max(freqs)
        maf = min(max_af, 1 - max_af)

        rows.append({
            "CHROM": chrom,
            "POS": pos,
            "N_ALLELES": n_alleles,
            "N_CHR": n_chr,
            "MAF": round(maf, 5),
        })

df = pd.DataFrame(rows)
df["CHROM"] = str(args.chrom)

df["MAF_PCT"] = df["MAF"].rank(pct=True)
df["MAF_PCT"] = round(df["MAF_PCT"], 5)
print(df.head())

# save
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, sep="\t", index=False)
print(f"Saved results to {output_path}")