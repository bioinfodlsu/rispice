import argparse, math
import numpy as np
import pandas as pd
from datasets import load_from_disk
from tqdm import tqdm
from pathlib import Path
from ...constants import HISTONE_MARKS, CHROMATIN_FEATURES

# FEATURES = HISTONE_MARKS
FEATURES = CHROMATIN_FEATURES

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute for the label co-occurrence in a file."
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Dataset (or parquet file) containing all the labels.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Save results to a tsv file.",
    )
    
    parser.add_argument("--parquet", action="store_true")
    
    return parser.parse_args()

def compute_cooccurrence_parquet(path):
    print(f"Loading parquet file from {path}")
    df = pd.read_parquet(path)
    
    labels = df[FEATURES]
    coocc = labels.T @ labels
    
    return coocc

def compute_cooccurrence(path, batch_size=64):
    print(f"Loading dataset from {path}")
    ds = load_from_disk(path)

    n_labels = len(ds["labels"][0])
    coocc = np.zeros((n_labels, n_labels), dtype=np.int64)

    n_batches = math.ceil(len(ds) / batch_size)

    for batch in tqdm(ds.iter(batch_size=batch_size), total=n_batches):
        labels = np.array(batch["labels"])
        coocc += labels.T @ labels

    # convert to df
    coocc_df = pd.DataFrame(
        coocc,
        index=FEATURES,
        columns=FEATURES
    )

    return coocc_df


args = parse_args()
print(args)

if args.parquet:
    df = compute_cooccurrence_parquet(args.input)
else:
    df = compute_cooccurrence(args.input)
    
df.index.name = "Feature"

# Setup output dir
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path, sep="\t")
