import argparse, pandas as pd
from cyvcf2 import VCF
from ..constants import NIPPONBARE_ID_TO_CHR_NUM, CHR_NUM_TO_CHR
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a VCF file to a SNP List for processing."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path VCF File.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Start base.",
    )
    parser.add_argument(
        "--output_fn",
        default="snp_list.tsv",
        help="File Name of the output",
    )
    parser.add_argument(
        "--nip_to_chrom",
        action="store_true",
        help="Given the Nipponbare ID, map it to a readable Chr code.",
    )
    parser.add_argument(
        "--num_to_chrom",
        action="store_true",
        help="Given the int format Chrom, map it to a readable Chr code.",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

vcf = VCF(args.input)

snps = []
for v in vcf:
    if len(v.ALT) > 1:
        raise ValueError(f"{v.ID} has multiple ALT alleles: {v.ALT}. Logic unsupported.")
    
    if args.nip_to_chrom:
        chrom = NIPPONBARE_ID_TO_CHR_NUM[v.CHROM]
    elif args.num_to_chrom:
        chrom = CHR_NUM_TO_CHR[int(v.CHROM)]
    else:
        chrom = v.CHROM
    
    snps.append({
        "chrom": chrom,
        "pos": v.POS,
        "id": v.ID,
        "ref": v.REF,
        "alt": v.ALT[0]
    })

df = pd.DataFrame(snps)
print(df)

# Setup output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / args.output_fn
df.to_csv(output_path, sep="\t", index=False)
print(f"Saved SNP List to {output_path}")