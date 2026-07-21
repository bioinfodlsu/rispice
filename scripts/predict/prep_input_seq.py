import argparse, pandas as pd
from pathlib import Path
from ..utils import SequenceUtils
from ..constants import NIPPONBARE_GENBANK_PATH, NIPPONBARE_ID_TO_CHR
from .utils import extract_seq

def parse_args():
    parser = argparse.ArgumentParser(description="Prepare the Input Sequences needed by the model.")
    parser.add_argument(
        "-f",
        "--fasta",
        default=NIPPONBARE_GENBANK_PATH,
        help="Path to the FASTA file containing the Reference Genome"
    )
    parser.add_argument(
        "-i",
        "--input",
        help="The SNP List file containing all the SNPs to be processed"
    )
    parser.add_argument(
        "--zero_based",
        action="store_true",
        help="Flag on whether to treat the position as zero-indexed. (Default: 1-based)"
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=500,
        help="The length of the Sequences to be generated. (Default: 500bp)"
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Where the output would be placed in."
    )
    parser.add_argument(
        "--output_fn",
        default="sequences.tsv",
        help="Where the output would be placed in."
    )
    return parser.parse_args()

class InputValidation():
    def is_alt_base_OK(alt_base:str):
        if len(alt_base) != 1:
            raise ValueError(f"Alt Base {alt_base} should be 1 base")
    

args = parse_args()
print(args)

snps_df = pd.read_csv(args.input, sep="\t")
snps = snps_df.to_dict(orient='records')

print(f"Accessing FASTA from {args.fasta}\n")
chroms = SequenceUtils.getSequences(args.fasta, NIPPONBARE_ID_TO_CHR.keys())

data = []
for snp in snps:
    print(f"Processing SNP: {snp}")
    # Validate
    InputValidation.is_alt_base_OK(snp["alt"])

    # Extract the Seq
    chr_num = int(snp["chrom"])
    target_chrom = chroms[chr_num-1]    # 0-index
    
    # Prepare Record
    record = { "chrom": f"Chr{chr_num}"}
    record.update(extract_seq(
        target_chrom,
        snp["alt"],
        snp["pos"],
        args.length,
        args.zero_based
    ))
    
    data.append(record)

# Turn the data into a df
df = pd.DataFrame(data)
print(df)

# Save to output
output_path = Path(args.output_dir) / args.output_fn
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, index=False, sep="\t")
print(f"Saved results to {output_path}")