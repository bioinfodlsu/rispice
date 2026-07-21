import argparse
import pandas as pd
import bioframe as bf

from scripts.utils import SequenceUtils
from scripts.constants import NIPPONBARE_GENBANK_PATH, NIPPONBARE_ID_TO_CHR

PVAR_COLS = ["CHR", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO"]

NIPPONBARE_GENOME_SEQ = SequenceUtils.getSequences(NIPPONBARE_GENBANK_PATH, NIPPONBARE_ID_TO_CHR.keys())
CHROM_LENS = {(index+1): len(chrom.sequence) for index, chrom in enumerate(NIPPONBARE_GENOME_SEQ)}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Sample SNPs genomewide given a tsv file config."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="tsv file containing all the paths to .pvar per chromosome and the counts. Required cols: pvar_path, cnt",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="vcf file containing all the SNPs genomewide.",
    )
    parser.add_argument(
        "--seed",
        default=42,
        type=int,
        help="Random State when sampling"
    )
    parser.add_argument(
        "-g",
        "--genes",
        default=".data/RAP_DB/rice_gene_ranges.tsv",
        help="Path to the gene ranges",
    )
    parser.add_argument(
        "--buffer",
        default=1000,
        type=int,
        help="Only extract SNPs after N bases from start and end of a chromosome"
    )
    
    return parser.parse_args()

def filter_non_coding_regions(snp_df, gene_df):
    """
    Uses bioframe to subtract gene regions from the SNP list.
    """
    # 1. Prepare SNP dataframe for bioframe
    # Bioframe needs 'chrom', 'start', 'end'
    snps = snp_df.copy()
    snps['chrom'] = snps['CHR'].astype(str).apply(
        lambda x: f"chr{int(x):02d}" if x.isdigit() else x
    )
    # VCF is 1-based [POS, POS]. Bioframe/BED is 0-based half-open [start, end)
    snps['start'] = snps['POS'] - 1
    snps['end'] = snps['POS']

    # 2. Subtract overlaps
    # bf.subtract returns only the intervals in 'snps' that do not overlap 'gene_df'
    non_coding_snps = bf.subtract(snps, gene_df)

    # 3. Restore original VCF columns
    return non_coding_snps[PVAR_COLS]


def sample_pvar(path, count, seed, gene_df, buffer, chr_lengths=CHROM_LENS, columns=PVAR_COLS):
    # 1. Load
    df = pd.read_csv(path, sep="\t", comment="#", header=None, names=columns)
    
    # 2. Quality Filter (NEW)
    # Only keep variants that passed QC. This removes 'snp_filter', 'LowQual', etc.
    if 'FILTER' in df.columns:
        df = df[df['FILTER'] == 'PASS'].copy()
    
    # 3. Boundary Filter (NEW)
    if buffer is not None:
        # Filter distance from start
        df = df[df['POS'] > buffer].copy()
        
        # Filter distance from end
        # We map the CHROM column to our lengths dictionary to get the limit for each row
        df['chr_len'] = df['CHR'].map(chr_lengths)
        df = df[df['POS'] < (df['chr_len'] - buffer)].copy()
        
        # Drop the temporary column
        df = df.drop(columns=['chr_len'])
        
    # 3. Biallelic & Non-deletion filter
    df = df[~df['ALT'].astype(str).str.contains(',') & (df['ALT'] != '*')].copy()
    
    # 4. Non-coding filter
    filtered_df = filter_non_coding_regions(df, gene_df)
    
    # 5. Sampling
    if len(filtered_df) < count:
        print(f"Warning: Only {len(filtered_df)} non-coding SNPs found in {path}.")
        return filtered_df
    
    return filtered_df.sample(n=count, random_state=seed)


def df_to_vcf(df, output_file, cols=PVAR_COLS):
    # Ensure correct column names
    df = df.copy()
    df.columns = cols  # enforce order if needed
    df = df.sort_values(["CHR", "POS"])
    df = df.rename(columns={"CHR": "#CHROM"})

    with open(output_file, "w") as f:
        # VCF metadata
        f.write("##fileformat=VCFv4.2\n")

        # Header
        f.write("\t".join(df.columns) + "\n")

        # Write rows
        df.to_csv(
            f,
            sep="\t",
            index=False,
            header=False,
            na_rep="."
        )


args = parse_args()
print(args)

# Read the genes
genes = pd.read_csv(args.genes, sep="\t")

# Read the tsv file
chroms = pd.read_csv(args.input, sep="\t")

all = []
for index, row in chroms.iterrows():
    print(f"Sampling {row.pvar_path}\t{row.cnt}")
    result = sample_pvar(row["pvar_path"], row["cnt"], args.seed, genes, args.buffer)
    
    all.append(result)

genomewide = pd.concat(all, ignore_index=True)

print(f"Saving VCF file to {args.output} with {len(genomewide)} total samples")
df_to_vcf(genomewide, args.output)
