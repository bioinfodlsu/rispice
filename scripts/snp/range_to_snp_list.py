import argparse, pandas as pd
from pathlib import Path
from ..utils import SequenceUtils
from ..constants import NIPPONBARE_ID_TO_CHR, BASES, CHR_NUM_TO_NIPPONBARE_ID

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.snp.range_to_snp_list",
        description="Generate a SNP list containing all possible A/C/G/T substitutions within a genomic interval."
    )

    parser.add_argument(
        "--chrom",
        required=True,
        type=int,
        help="Chromosome number (1-12).",
    )

    parser.add_argument(
        "--start",
        required=True,
        type=int,
        help="Start genomic position (1-based, inclusive).",
    )

    parser.add_argument(
        "--end",
        required=True,
        type=int,
        help="End genomic position (1-based, inclusive).",
    )

    parser.add_argument(
        "-f",
        "--fasta",
        required=True,
        help=(
            "Reference genome FASTA file "
            "(GenBank assembly GCA_001433935.1)."
        ),
    )

    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where the output file will be written.",
    )

    parser.add_argument(
        "--output_fn",
        default="snp_list.tsv",
        help="Name of the output SNP list file (default: %(default)s).",
    )

    # parser.add_argument(
    #     "--override_chrom",
    #     action="store_true",
    #     help=(
    #         "Convert Nipponbare accession IDs in the FASTA "
    #         "to chromosome numbers (Chr1-Chr12)."
    #     ),
    # )

    parser.add_argument(
        "--use_nipponbare_id",
        action="store_true",
        help=(
            "Store chromosome identifiers using Nipponbare accession IDs "
            "instead of chromosome numbers."
        ),
    )

    return parser.parse_args()

args = parse_args()
print(args)

print(f"Accessing FASTA from {args.fasta}\n")
chroms = SequenceUtils.getSequences(args.fasta, NIPPONBARE_ID_TO_CHR.keys())

# Correct indexing
zero_based_start = args.start - 1
zero_based_end = args.end           # inclusive in 1-based indexing

# Get SubSequence
target_chrom = chroms[args.chrom-1] # 0-index
subseq = target_chrom.sequence[zero_based_start:zero_based_end]

snps = []
for i, base in enumerate(subseq):
    pos = args.start + i    # Get 1-Index Position
    
    for alt in BASES:
        snps.append({
            "chrom": CHR_NUM_TO_NIPPONBARE_ID[args.chrom] if args.use_nipponbare_id else args.chrom,
            "pos": pos,
            "id": ".",
            "ref": base,
            "alt": alt
        })

df = pd.DataFrame(snps)
print(df)

# Setup output_dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / args.output_fn
df.to_csv(output_path, sep="\t", index=False)
print(f"Saved SNP List to {output_path}")