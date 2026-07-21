import argparse, os, numpy as np, pandas as pd
from datasets import load_from_disk, concatenate_datasets
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
from ..helper import get_features
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Given a directory containing all datasets for each chromosome, extract N number of samples in total out of all datasets while maintaining multilabel balance.")
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
        default="subsample_ds",
        dest="ds_name",
        help="Name of the merged dataset"
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        required=True,
        help="Number of entries to be randomly taken per dataset. If not set, it takes all entries."
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=42,
        help="Random Seed to be used when taking random N entries. (Default: 42)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="If flagged as strict, it would enfore perfectly equal count subsamples."
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

# Define chromosome ids
chrom_ids = list(range(1,13))
input_path = Path(args.input_dir)
chr_dir = [x for x in input_path.iterdir() if x.is_dir()]

print(f"Loading datasets from {args.input_dir}")
chrom_ds = {
    dir.stem: load_from_disk(dir)
    for dir in chr_dir
}
print(f"Loaded {len(chrom_ds)} datasets")

print(f"Computing quotas per chromosome")
chrom_sizes = {chr_id: len(ds) for chr_id, ds in chrom_ds.items()}
total = sum(chrom_sizes.values())

chrom_quota = {
    chr_id: int(args.count * chrom_sizes[chr_id] / total)
    for chr_id in chrom_sizes
}

# Distribute "remainders" for exact sample counts per chrom
diff = args.count - sum(chrom_quota.values())
if diff > 0:
    # distribute remaining samples to largest chromosomes
    for chr_id in sorted(chrom_sizes, key=chrom_sizes.get, reverse=True):
        if diff == 0:
            break
        chrom_quota[chr_id] += 1
        diff -= 1
        
# Assert that total of chrom_quotas == expected count
assert sum(chrom_quota.values()) == args.count  
print(chrom_quota)

print("Subsampling per chromosome (multilabel-stratified)...")

subsample_chrom_ds = []
for chr_id, ds in chrom_ds.items():
    n_chr = chrom_quota[chr_id]

    stratified_ds = stratified_subsample_per_chrom(
        ds,
        n_samples=n_chr,
        label_field="labels",
        seed=args.seed,
    )
    print(f"Chr{chr_id}: {len(ds)} → Q:{n_chr} | A:{len(stratified_ds)}")

    subsample_chrom_ds.append(stratified_ds)

print("Concatenating subsample datasets...")
subsample_ds = concatenate_datasets(subsample_chrom_ds)

print(f"Final subsample dataset size: {len(subsample_ds)}")
if args.strict:
    assert len(subsample_ds) == args.count

# Assert similar mean as full dataset
print("Asserting similarity between subset and full datasets...")
full_ds = concatenate_datasets(list(chrom_ds.values()))

print("Computing full dataset mean...")
full = label_mean(full_ds)
print("Computing subsample dataset mean...")
sub  = label_mean(subsample_ds)

print("Computing label counts...")
ones = label_count(subsample_ds)
zeros = args.count - ones

stat = pd.DataFrame({
    "Features": get_features(args.features_path),
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