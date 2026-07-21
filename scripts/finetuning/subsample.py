import argparse
import numpy as np
import pandas as pd
from datasets import load_from_disk
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
from pathlib import Path
from ..helper import get_features

def parse_args():
    parser = argparse.ArgumentParser(
        description="Given a dataset dir, extract N number of samples in total while maintaining multilabel distribution."
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Path containing the HuggingFace `Dataset` to be subsampled with Iterative Stratification.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Path where the subsampled `Dataset` would be stored.",
    )
    parser.add_argument(
        "-n",
        "--name",
        default="subsample_ds",
        dest="ds_name",
        required=True,
        help="Path where the subsampled `Dataset` would be stored.",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        required=True,
        help="Number of entries to be randomly taken per dataset.",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=42,
        help="Random Seed to be used when taking random N entries. (Default: 42)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the stratified subsample into disk."
    )
    parser.add_argument(
        "--features_path",
        default=".data2/prep/constant/features.csv",
        help="Path to csv file containing the list of all features to process (ensure sorting.).",
    )
    return parser.parse_args()


def stratified_subsample_per_chrom(
    dataset,
    n_samples,
    label_field="labels",
    seed=42,
):
    if n_samples >= len(dataset):
        return dataset

    y = np.array(dataset[label_field])
    frac = n_samples / len(dataset)

    msss = MultilabelStratifiedShuffleSplit(
        n_splits=1,
        test_size=frac,
        random_state=seed,
    )

    _, idx = next(msss.split(np.zeros(len(dataset)), y))
    return dataset.select(idx.tolist())


def label_mean(ds, label_field="labels"):
    return np.array(ds[label_field]).mean(axis=0)


def label_count(ds, label_field="labels"):
    return np.array(ds[label_field]).sum(axis=0)


args = parse_args()
print(args)

FEATURES = get_features(args.features_path)

print(f"Loading dataset from {args.input_dir}")
ds = load_from_disk(args.input_dir)
print(f"Loaded {ds}")

print(f"Subsampling dataset (multilabel-stratified) {len(ds):,} → {args.count:,}...")
subsample_ds = stratified_subsample_per_chrom(
    ds,
    n_samples=args.count,
    label_field="labels",
    seed=args.seed,
)
print(f"Final subsample dataset size: {len(subsample_ds):,}")
assert len(subsample_ds) == args.count

# Assert similar mean as full dataset
print("Asserting similarity between subset and full datasets...")
print("Computing full dataset mean...")
full = label_mean(ds)
print("Computing subsample dataset mean...")
sub  = label_mean(subsample_ds)

print("Computing label counts...")
ones = label_count(subsample_ds)
zeros = args.count - ones

stat = pd.DataFrame({
    "features": FEATURES,
    "Full": full,
    "Subsample": sub,
    "Δ (Sub - Full)": sub - full,
    "Subsample 1s": ones,
    "Subsample 0s": zeros
})
print(stat.to_string(index=False, float_format="%.6f"))

# Save to Disk
if args.save:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{args.ds_name}"    # Dataset name
    print(f"Saving subsample dataset to {output_path}")
    subsample_ds.save_to_disk(output_path)

    # Save stats
    stats_dir = output_dir / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)

    stats_path = stats_dir / f"{args.ds_name}.csv"
    print(f"Saving stats to {stats_path}")
    stat.to_csv(stats_path, index=False)