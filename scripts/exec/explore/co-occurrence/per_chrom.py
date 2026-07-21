import subprocess
from pathlib import Path

BASE_IN_DIR = Path("data/finetune/histone/chr")
BASE_OUT_DIR = Path("analysis/explore/co-occurrence/proposal/chr")

for i in range(1,13):
    in_dir = BASE_IN_DIR / f"{i}.parquet"
    out_dir = BASE_OUT_DIR / f"{i}.tsv"
    
    print(f"[START {i}] Processing {in_dir}")
    subprocess.run([
        "python", "-m", "scripts.explore.co-occurrence.matrix",
        "-i", in_dir,
        "-o", out_dir,
        "--parquet"
    ])
    print(f"[END {i}]Finished {in_dir}")