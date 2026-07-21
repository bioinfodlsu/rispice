import argparse
from datasets import load_from_disk
from pathlib import Path
from ..constants import MAX_LENGTH, KMERS
from ..utils import PreTrainingUtils

def parse_args():
    parser = argparse.ArgumentParser(description="Kmerize a set of parquet files")
    parser.add_argument(
        "-i",
        "--input_ds",
        required=True,
        help="Path containing the dataset (HuggingFace) to be kmerized.",
    )
    parser.add_argument(
        "-k",
        "--kmer",
        required=True,
        type=int,
        help="Set the value K for the kmer value. Supported Values: 3, 4, 5, 6.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Path where the kmerized dataset would be placed.",
    )

    args = parser.parse_args()
    return args

def kmerize_batch(batch, k, max_kmers=MAX_LENGTH):
    batch["seq"] = [
        PreTrainingUtils.kmerize(seq, k=k, max_kmers=max_kmers)
        for seq in batch["seq"]
    ]
    return batch

def is_valid_kmer(k, valid_kmers=KMERS):
    return k in valid_kmers

def input_validation(args):
    # kmer
    if not is_valid_kmer(args.kmer):
        raise Exception(f"{args.kmer}-mers are not supported. Should be in [3,4,5,6]")


args = parse_args()
print(args)

# Validate Input
input_validation(args)

print(f"Loading dataset from {args.input_ds}")
ds_path = Path(args.input_ds)
ds = load_from_disk(ds_path)

ds = ds.map(
    kmerize_batch,
    batched=True,
    fn_kwargs={"k": args.kmer},
    desc=f"K-merizing sequences (K={args.kmer})"
)

# Save to disk
output_path = Path(args.output_dir)
output_path.parent.mkdir(parents=True, exist_ok=True)   # Create parent dirs

print(f"Saving kmerized dataset to {output_path}")
ds.save_to_disk(output_path)
