import subprocess
from pathlib import Path

SEQ_LEN = "1000"
BASE_IN_DIR = Path(".data2/set5/chr")
BASE_OUT_DIR = Path("analysis2/prevalence")

COLUMN_FILE = Path(".data2/prep/constant/features.csv")

for i in range(1,13):
    in_dir = BASE_IN_DIR / SEQ_LEN / f"{i}.parquet"
    out_dir = BASE_OUT_DIR / SEQ_LEN / "chr" / f"{i}.csv"
    
    print(f"[START {i}] Processing {in_dir}")
    subprocess.run([
        "python", "-m", "scripts.analysis.get_label_ratio",
        "-f", in_dir,
        "-c", COLUMN_FILE,
        "-o", out_dir,
        "--overwrite"
    ])
    print(f"[END {i}]Finished {in_dir}")