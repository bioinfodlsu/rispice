import argparse
import pandas as pd

COLS = ["chrom", "source", "type", "start", "end", "score", "strand", "phase", "attrs"]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract the list of genes and its ranges given a gff file."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the gff file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="output file where all the ranges would be saved.",
    )
    
    return parser.parse_args()

def get_rice_gene_ranges(gff_path, cols=COLS) -> pd.DataFrame:
    # Read GFF, skipping header lines
    df = pd.read_csv(gff_path, sep="\t", comment="#", header=None, names=cols)
    
    # Filter for genes only
    genes = df[df["type"] == "gene"].copy()
    
    # Extract the ID from the attributes column (ID=Os01g0100100;Name=...)
    genes["gene_id"] = genes["attrs"].str.extract(r'ID=([^;]+)')
    
    return genes[["gene_id", "chrom", "start", "end", "strand"]]

args = parse_args()
print(args)

print(f"Processing {args.input}")
genes = get_rice_gene_ranges(args.input)
print(f"Extracted {len(genes):,} genes")

genes.to_csv(args.output, sep="\t", index=False)
print(f"Saved to {args.output}")