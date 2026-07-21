import subprocess, pandas as pd
from pathlib import Path

SEQ_LEN = "1000"
BASE_MARK_DIR = Path(f"analysis2/prevalence/{SEQ_LEN}/per_feature")
BASE_OUT_DIR = Path(f"figures2/prevalence/{SEQ_LEN}/per_feature")

COLUMN_FILE = Path(".data2/prep/constant/features.csv")

histone_marks = pd.read_csv(COLUMN_FILE)["features"].tolist()
for i, mark in enumerate(histone_marks, start=1):
    mark_file = BASE_MARK_DIR / f"{mark}.csv"
    
    module = "scripts.analysis.visualize.label_ratio.per_mark_stacked_bar"
    print(f"[START {i}] Processing {mark_file}")
    subprocess.run([
        "python", "-m", module,
        "-f", mark_file,
        "-o", BASE_OUT_DIR
    ])
    print(f"[END {i}]Finished {mark_file}")
