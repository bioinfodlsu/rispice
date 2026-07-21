import argparse
import pandas as pd
from pathlib import Path
from typing import List

from ..utils import (
    SequenceUtils,
    SequenceHandler
)
from ..constants import (
    NIPPONBARE_GENBANK_PATH,
    NIPPONBARE_ID_TO_CHR
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Label Processing given a dir containing coverage files of an Annotation."
    )
    parser.add_argument(
        "-d",
        "--dir",
        required=True,
        help="Directory where all the processed results will be stored."
    )
    parser.add_argument(
        "-b",
        "--bin",
        type=int,
        required=True,
        help="Length (in bp) of the bins (core regions) to be generated"
    )
    parser.add_argument(
        "-e",
        "--extension",
        type=int,
        required=True,
        help="Length (in bp) to be extended forward and backward of bins"
    )
    parser.add_argument(
        "-r",
        "--ref_genome",
        default=NIPPONBARE_GENBANK_PATH,
        help="Path to the Nipponbare ref genome's fasta file.",
    )
    parser.add_argument(
        "--N_threshold",
        type=float,
        default=0,
        help="Filter the samples if it contains this ratio of N-nucleotides (ambiguous).",
    )
    return parser.parse_args()

def divideToBins(genome:List[SequenceHandler], bin_size:int):
    """Divide the genome into X-bp bins."""
    SAMPLES = []
    total_count = 0
    for chrom in genome:
        chr_name = NIPPONBARE_ID_TO_CHR[chrom.name]
        bins = chrom.divideToBins(bin_size, bin_size)
        
        # Update sample list and total_count ref
        SAMPLES.append(bins)
        total_count += len(bins)
        print(f"Binning {chr_name}\t{len(bins):,} samples")
        
    print(f"TOTAL: {total_count:,}")
    return SAMPLES

def transformToDict(sample:SequenceHandler, chromosome:int) -> dict:
    return {
        "chr": chromosome,
        "start": sample.start_index,    # Use this indexing as per BED standard 
        "end": sample.end_index + 1,    # (inclusive start, exclusive end)
        "seq": str(sample.sequence)
    }

def df_to_bed(df, out_path):
    """Convert dataframe to bed file."""
    bed_df = df[["chr", "start", "end"]].copy()
    bed_df["chr"] = "Chr" + df["chr"].astype(str)
    bed_df["start"] = bed_df["start"].astype(int)
    bed_df["end"] = bed_df["end"].astype(int)

    # Write BED (tsv, no header)
    bed_df.to_csv(out_path, sep="\t", header=False, index=False)

    return out_path

args = parse_args()
print(args)

SAMPLE_SIZE = args.bin + (args.extension * 2)
# Summarize
print(f"Processing {args.bin}bp core regions, {SAMPLE_SIZE}bp sequence length")

# Import the Reference Genome for Nipponbare (Oryza Sativa)
NIPPONBARE_GENOME_SEQ = SequenceUtils.getSequences(
    args.ref_genome, NIPPONBARE_ID_TO_CHR.keys()
)

# Get the samples (bins)
samples = divideToBins(NIPPONBARE_GENOME_SEQ, args.bin)

# Extend to get final sample sizes
for index, chrom in enumerate(NIPPONBARE_GENOME_SEQ, 0):
    chr_name = NIPPONBARE_ID_TO_CHR[chrom.name]
    print(f"Extending bins to {SAMPLE_SIZE}bp long of {chr_name}\t({args.extension}bp forwards and backwards)")
    ref_seq = NIPPONBARE_GENOME_SEQ[index]
        
    # Extend Forward and Backward
    bins = samples[index]
    SequenceUtils.extendBins(bins, ref_seq.sequence, args.extension, False)
    SequenceUtils.extendBinsBackward(bins, ref_seq.sequence, args.extension, False)
    
# Filter Samples with N nucleotides
stats = []
print(f"Dropping samples where its N nucleotides are more than {args.N_threshold}.")
for index, chromosome in enumerate(NIPPONBARE_ID_TO_CHR.keys()):
    before = len(samples[index])
    samples[index] = SequenceUtils.filterAmbiguity(samples[index], args.N_threshold)
    
    stats.append({
        "chr": chromosome,
        "before": before,
        "after": len(samples[index]),
        "change": before - len(samples[index])
    })
    
info = pd.DataFrame(stats)
print(info)

# Store sample data into pandas df
all_samples = []
print("Transforming samples to dataframe")
for index, samples in enumerate(samples):
    print(f"*Processing Chr{index+1}")
    chr_samples = [transformToDict(sample, index+1) for sample in samples]
    all_samples.extend(chr_samples)

df = pd.DataFrame(all_samples)
print(df)

# Save data to output_dir
print(f"Saving Outputs:")
output_path = Path(args.dir)
output_path.mkdir(parents=True, exist_ok=True)

bed_path = output_path / "core_regions.bed"
stats_path = output_path / "filter_stats.tsv"
df_to_bed(df, bed_path) # Core regions
info.to_csv(stats_path, sep="\t") # Filter stats

print(f"Saved {bed_path}")
print(f"Saved {stats_path}")

# Chromosomes
for chrom in df["chr"].unique():
    chr_path = output_path / f"{chrom}.parquet"
    df[df["chr"] == chrom].to_parquet(
        chr_path,
        engine="pyarrow",
        compression="zstd",
        compression_level=3
    )
    print(f"Saved {chr_path}")
