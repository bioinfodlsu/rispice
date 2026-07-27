import argparse, pandas as pd
from pathlib import Path
from ..utils import SequenceUtils
from ..constants import NIPPONBARE_ID_TO_CHR
from .utils import extract_seq

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.predict.generate_sequences",
        description=(
            "Generate reference and alternate DNA sequences centred on input SNPs "
            "for downstream RiSPICE prediction.\n\n"
            "Note: The reference genome should correspond to the Nipponbare "
            "IRGSP-1.0 assembly (GenBank accession GCA_001433935.1)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-f",
        "--fasta",
        help=(
            "Reference genome FASTA file (GenBank accession GCA_001433935.1). "
        ),
    )

    parser.add_argument(
        "-i",
        "--input",
        help=(
            "Input SNP file containing the variants to process."
        ),
    )

    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=1000,
        help=(
            "Length (bp) of the generated reference and alternate sequences. "
            "(default: 1000)"
        ),
    )

    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where output files will be written.",
    )

    parser.add_argument(
        "--output_fn",
        default="sequences.tsv",
        help=(
            "Name of the output TSV file. "
            "(default: sequences.tsv)"
        ),
    )

    parser.add_argument(
        "--zero_based",
        action="store_true",
        help=(
            "Treat SNP coordinates as 0-based. "
            "By default, positions are interpreted as 1-based."
        ),
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