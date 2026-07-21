import subprocess, pandas as pd
from pathlib import Path

BASE_IN_DIR = Path(".data2/prep/coverages5")
BASE_OUT_DIR = Path(".data2/prep/labels5")
FEATURES_PATH = Path(".data2/prep/constant/features.csv")

def get_features(path=FEATURES_PATH, key="features"):
    df = pd.read_csv(path)
    return df[key].to_list()


CHROMATIN_FEATURES = get_features()
SEQ_LEN = "750"

for feature in CHROMATIN_FEATURES:
    in_path = BASE_IN_DIR / SEQ_LEN / feature
    out_path = BASE_OUT_DIR / SEQ_LEN / f"{feature}.tsv"
    stats_path =  BASE_OUT_DIR / SEQ_LEN / "stats" / f"{feature}.tsv"

    print(f"[START {SEQ_LEN}bp:{feature}] Processing {in_path}")
    subprocess.run([
        "python", "-m", "scripts.data_prep.label_samples",
        "-i", in_path,
        "-o", out_path,
        "--stats_path", stats_path
    ])
    print(f"[END {SEQ_LEN}bp:{feature}] Finished {out_path} | {stats_path}")

    
