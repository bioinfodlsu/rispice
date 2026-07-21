import argparse, os
import pandas as pd
from ..constants import KMERS, MAX_LENGTH
from ..utils import PreTrainingUtils


def parse_args():
    parser = argparse.ArgumentParser(description="Kmerize a set of parquet files")
    parser.add_argument(
        "-d",
        "--data_path",
        required=True,
        help="Path containing all the files to be kmerized.",
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
        "--output_path",
        required=True,
        help="Path where the kmerized outputs will be placed.",
    )
    parser.add_argument(
        "-c",
        "--column",
        default="seq",
        help="Column containing the sequence to kmerize.",
    )
    parser.add_argument(
        "-n",
        "--new_col",
        default="kmerized",
        help="Column where the kmerized seq is stored.",
    )

    args = parser.parse_args()
    return args


def is_valid_kmer(k, valid_kmers=KMERS):
    return k in valid_kmers


def input_validation(args):
    # kmer
    if not is_valid_kmer(args.kmer):
        raise Exception(f"{args.kmer}-mers are not supported. Should be in [3,4,5,6]")

    # output path
    os.makedirs(args.output_path, exist_ok=True)


args = parse_args()

# Validate Input
input_validation(args)

# Retrieve the Files to Process
files = [
    f
    for f in os.listdir(args.data_path)
    if os.path.isfile(os.path.join(args.data_path, f))
]

# Processing
for file in files:
    print(f"processing {file}")
    path_to_file = os.path.join(args.data_path, file)
    df = pd.read_parquet(path_to_file)
    X = df[args.column].values.tolist()

    print(f"* kmerizing with {len(X):,} entries")
    X = [PreTrainingUtils.kmerize(seq, k=args.kmer, max_kmers=MAX_LENGTH) for seq in X]
    df[args.new_col] = X

    print(f"* saving {file} to {args.output_path}")
    df.to_parquet(
        os.path.join(args.output_path, file),
        engine="pyarrow",
        compression="zstd",
        compression_level=3,
    )
