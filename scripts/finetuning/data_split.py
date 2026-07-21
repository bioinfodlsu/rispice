import argparse, os
import pandas as pd
import numpy as np
from ..helper import get_features
from sklearn.model_selection import train_test_split
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
from datasets import Dataset


def parse_args():
    parser = argparse.ArgumentParser(description="Kmerize a set of parquet files")
    parser.add_argument(
        "-d",
        "--data_path",
        required=True,
        help="Path containing all the files to be split into train, test, and validation sets.",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        required=True,
        help="Path where the split data outputs will be placed.",
    )
    parser.add_argument(
        "-c",
        "--column",
        default="seq",
        help="Set the specific column to be split (X).",
    )
    parser.add_argument(
        "--features_path",
        default=".data2/prep/constant/features.csv",
        help="Path to csv file containing the list of all features to process (ensure sorting.).",
    )
    parser.add_argument(
        "-t",
        "--test_size",
        type=float,
        default=0.2,
        help="Set the test size when splitting.",
    )
    parser.add_argument(
        "-v",
        "--val_size",
        type=float,
        default=0.2,
        help="Set the validation size when splitting.",
    )
    parser.add_argument(
        "--random_state", type=int, default=42, help="Set the random state value."
    )
    parser.add_argument(
        "--iterative_stratification",
        action="store_true",
        help="Flag the script to use MultilabelStratifiedShuffleSplit when splitting the dataset.",
    )
    parser.add_argument(
        "--chrom_split",
        action="store_true",
        help="Flag the script to use Chromosome-Specific Strategy when splitting the data."
    )
    parser.add_argument(
        "--test_chrom",
        type=float,
        default=6,
        help="Select the chromosome for the Test Set. Only used when `--chrom_split` flag is set.",
    )
    parser.add_argument(
        "--val_chrom",
        type=float,
        default=7,
        help="Select the chromosome for the Validation Set. Only used when `--chrom_split` flag is set.",
    )

    args = parser.parse_args()
    return args


def is_valid_annotation_type(annotation, valid_types=["histone", "chromatin", "all"]):
    return annotation in valid_types


def input_validation(args):
    # output path
    os.makedirs(args.output_path, exist_ok=True)


def gen(split_X, split_y):
    for x, y in zip(split_X, split_y):
        yield {"seq": x, "labels": y}


def save_to_disk(dataset, dataset_type, file_name, output_dir):
    dir = os.path.join(output_dir, dataset_type)
    os.makedirs(dir, exist_ok=True)
    dataset.save_to_disk(os.path.join(dir, f"{file_name}"))


def split(X, y, test_size, random_state):
    """Use sklearn's train_test_split when splitting the dataset"""
    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def split_multilabel(X, y, test_size, val_size, random_state):
    """Use MultilabelStratifiedShuffleSplit when splitting the dataset"""
    # ---- Train+Val / Test ----
    msss_test = MultilabelStratifiedShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=random_state,
    )
    trainval_idx, test_idx = next(msss_test.split(X, y))

    X_trainval, X_test = X[trainval_idx], X[test_idx]
    y_trainval, y_test = y[trainval_idx], y[test_idx]

    # ---- Train / Val (relative to trainval) ----
    val_fraction = val_size / (1.0 - test_size)

    msss_val = MultilabelStratifiedShuffleSplit(
        n_splits=1,
        test_size=val_fraction,
        random_state=random_state,
    )
    train_idx, val_idx = next(msss_val.split(X_trainval, y_trainval))

    X_train, X_val = X_trainval[train_idx], X_trainval[val_idx]
    y_train, y_val = y_trainval[train_idx], y_trainval[val_idx]

    return X_train, X_val, X_test, y_train, y_val, y_test


args = parse_args()
print(args)

# Validate Input
input_validation(args)

# Retrieve the Files to Process
files = [
    f
    for f in os.listdir(args.data_path)
    if os.path.isfile(os.path.join(args.data_path, f))
]

label_cols = get_features(args.features_path)

# all_lists
all_train_X = []
all_val_X = []
all_test_X = []
all_train_y = []
all_val_y = []
all_test_y = []


# stats
all_stats = []
CHROMOSOMES = [str(i) for i in range(1, 13)]
for file in files:
    # get filename
    filename = file.split(".")[0]
    
    # Support case where there are "extra files" in the dir
    if filename not in CHROMOSOMES:
        print(f"Skipping non chr file: {filename}.")
        continue
    
    print(f"Processing chr{filename} from {file}")
    
    path_to_file = os.path.join(args.data_path, file)
    df = pd.read_parquet(path_to_file)

    X = df[args.column].to_numpy()
    y = df[label_cols].to_numpy()

    # Train-Test Split
    print(f"* splitting {file}") 
    if args.iterative_stratification:
        X_train, X_val, X_test, y_train, y_val, y_test = split_multilabel(
            X,
            y,
            test_size=args.test_size,
            val_size=args.val_size,
            random_state=args.random_state,
        )
    elif args.chrom_split:
        # Set everything to None first
        X_train, y_train = None, None
        X_test, y_test = None, None
        X_val, y_val = None, None
        
        # Place chr to the specific sets
        if int(filename) == args.test_chrom:
            X_test, y_test = X, y
        elif int(filename) == args.val_chrom:
            X_val, y_val = X, y
        else:
            X_train, y_train = X, y
    else:
        X_train, X_test, y_train, y_test = split(
            X, y, test_size=args.test_size, random_state=args.random_state
        )
        X_train, X_val, y_train, y_val = split(
            X_train, y_train, test_size=args.val_size, random_state=args.random_state
        )

    print(f"* saving dataset")
    # save to data
    # Train Set
    if X_train is not None and y_train is not None:
        dataset = Dataset.from_generator(lambda: gen(X_train, y_train), split="train")
        save_to_disk(dataset, "train", filename, args.output_path)

    # Test Set
    if X_test is not None and y_test is not None:
        dataset = Dataset.from_generator(lambda: gen(X_test, y_test), split="test")
        save_to_disk(dataset, "test", filename, args.output_path)

    # Validation Set
    if X_val is not None and y_val is not None:
        dataset = Dataset.from_generator(lambda: gen(X_val, y_val), split="val")
        save_to_disk(dataset, "val", filename, args.output_path)

    # Specify stats
    all_stats.append(
        {
            "file": file,
            "orig_size": len(X),
            "train_cnt": len(X_train) if X_train is not None else 0,
            "val_cnt": len(X_val) if X_val is not None else 0,
            "test_cnt": len(X_test) if X_test is not None else 0,
        }
    )

    # Clear memory to avoid OOM
    del df, X, y, X_train, X_test, X_val, y_train, y_test, y_val

# Summarize stats
print("Saving stats...")
stats_df = pd.DataFrame(all_stats)
stats_df.to_csv(os.path.join(args.output_path, "stats.csv"), index=False)
