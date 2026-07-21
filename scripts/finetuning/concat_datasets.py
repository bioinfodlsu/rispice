import argparse, os
from datasets import load_from_disk, concatenate_datasets
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Execute tokenize script for all chromosomes")
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Path containing all the datasets to be stored. It is assumed that it contains folders 1-12 (chromosomes)."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Path where the resulting tokenized datasets would be stored"
    )
    parser.add_argument(
        "-n",
        "--name",
        default="merged_ds",
        dest="ds_name",
        help="Name of the merged dataset"
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        help="Number of entries to be randomly taken per dataset. If not set, it takes all entries."
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=42,
        help="Random Seed to be used when taking random N entries. (Default: 42)"
    )
    return parser.parse_args()

def input_validation(args):
    # output path
    os.makedirs(args.output_dir, exist_ok=True)
    
args = parse_args()
print(args)

input_validation(args)

INPUT_DIR = Path(args.input_dir)
DATASETS = [p for p in INPUT_DIR.iterdir() if p.is_dir()]

# instantiate all datasets
print(f"Loading {len(DATASETS)} datasets from disk...")
all_ds = []
for ds in DATASETS:
    if args.count is None:
        all_ds.append(load_from_disk(ds))
    else:
        all_ds.append(load_from_disk(ds).shuffle(seed=args.seed).select(range(args.count)))

print("Concatenating datasets...")
merged_ds = concatenate_datasets(all_ds)

print("Shuffling the dataset...")
merged_ds = merged_ds.shuffle(seed=args.seed)

path = os.path.join(args.output_dir, args.ds_name)
print(f"Saving to disk in dir: {path}...")
merged_ds.save_to_disk(path)