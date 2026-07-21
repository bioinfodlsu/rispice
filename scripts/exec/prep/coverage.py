from pathlib import Path
from pybedtools import BedTool

SEQ_DIR = Path(".data2/prep/sequences")
PEAKS_DIR = Path(".data2/prep/profiles/peaks5")
OUTPUT_DIR = Path(".data2/prep/coverages5")

def get_coverage(peaks_file: str, sample_file: str):
    """Uses pybedtools to retrieve the coverage information of the samples given peaks."""
    peaks = BedTool(peaks_file)
    query = BedTool(sample_file)
    coverage = query.coverage(peaks)  # use pybedtools to get coverage info

    # covert coverage into a dataframe
    cov_df = coverage.to_dataframe(
        names=[
            "chrom",
            "start",
            "end",
            "num_overlaps",
            "bases_covered",
            "interval_length",
            "fraction_covered",
        ]
    )
    cov_df["percent_covered"] = cov_df["fraction_covered"] * 100

    return cov_df

# seq_subdirs = [x for x in SEQ_DIR.iterdir() if x.is_dir()]
seq_subdirs = [SEQ_DIR / "500", SEQ_DIR / "750"]    # while only testing 1000
peaks_subdirs = [x for x in PEAKS_DIR.iterdir() if x.is_dir()]

for seq in seq_subdirs:
    print(f"[Processing {seq.stem}bp sequence length]")
    
    core_regions_f = seq / "core_regions.bed"
    
    for feature in peaks_subdirs:
        print(f"*[{feature.stem}]")
        files = [p for p in feature.iterdir() if p.is_file()]
        
        for f in files:
            print(f"**{f.name}")
            df = get_coverage(f, core_regions_f)
            
            # Save to result
            output_path = OUTPUT_DIR / seq.stem / feature.stem / f"{f.stem}.tsv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, sep="\t", index=False)