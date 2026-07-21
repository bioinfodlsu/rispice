import argparse
import pandas as pd

CORE_SNP_DS = ".data/SNP_Seek/404K_CoreSNP/base_filtered_v0.7_0.8_10kb_1_0.8_50_1.bim"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Get the REF and ALT alleles of a region."
    )
    parser.add_argument(
        "--chr",
        required=True,
        type=int,
        help="Chromosome.",
    )
    parser.add_argument(
        "--start",
        required=True,
        type=int,
        help="Start base.",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=int,
        help="End base.",
    )
    parser.add_argument(
        "--bim_path",
        default=CORE_SNP_DS,
        help="Path to the .bim file"
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

bim = pd.read_csv(
    args.bim_path,
    sep="\t",
    header=None,
    names=["CHR", "SNP", "CM", "BP", "A1", "A2"]
)

region = bim[
    (bim["CHR"] == args.chr) &
    (bim["BP"] >= args.start) &
    (bim["BP"] <= args.end)
]

print("Number of SNPS:", len(region))
print(region)