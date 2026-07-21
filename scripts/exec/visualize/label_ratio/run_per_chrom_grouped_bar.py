import subprocess
from pathlib import Path

SEQ_LEN = "1000"
BASE_CHROM_DIR = Path(f"analysis2/prevalence/{SEQ_LEN}/chr")
BASE_OUT_DIR = Path(f"figures2/prevalence/{SEQ_LEN}/per_chrom_counts")

COLUMN_FILE = Path(".data2/prep/constant/features.csv")

for i in range(1,13):
    chrom_file = BASE_CHROM_DIR / f"{i}.csv"
    
    module = "scripts.analysis.visualize.label_ratio.per_chrom_grouped_bar"
    print(f"[START {i}] Processing {chrom_file}")
    subprocess.run([
        "python", "-m", module,
        "-f", chrom_file,
        "-c", COLUMN_FILE,
        "-o", BASE_OUT_DIR
    ])
    print(f"[END {i}]Finished {chrom_file}")