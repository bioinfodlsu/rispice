import argparse
import pandas as pd
from pathlib import Path
from ..helper import get_features

CHROMOSOMES = range(1,13)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Given the labels per chromatin feature, finalize the fine tuning dataset per chrom."
    )
    parser.add_argument(
        "-l",
        "--labels",
        required=True,
        help="Path to the dir containing all the coverage files to be processed.",
    )
    parser.add_argument(
        "-s",
        "--sequences",
        required=True,
        help="Path to the dir containing all the sequence parquet files to be processed.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Path to the dir containing all the sequence parquet files to be processed.",
    )
    parser.add_argument(
        "--features_path",
        default=".data2/prep/constant/features.csv",
        help="Path to csv file containing the list of all features to process (ensure sorting.).",
    )
    return parser.parse_args()

args = parse_args()
print(args)

CHROMATIN_FEATURES = get_features(args.features_path)
BASE_LABEL_PATH = Path(args.labels)
BASE_SEQ_PATH = Path(args.sequences)

# Get combined seq dataset
print("Getting all sequence chrom dataframes...")
dfs = []
for chrom in CHROMOSOMES:
    chrom_path = BASE_SEQ_PATH / f"{chrom}.parquet"
    
    print(f"Loading {chrom_path}")
    df = pd.read_parquet(chrom_path)
    dfs.append(df)

print("Merging all dataframes...")
merged_df = pd.concat(dfs, ignore_index=True)
print(f"Total Entries: {len(merged_df)}")

# Get all labels
print("Getting all labels per feature dataframes...")
label_dict = {}
stats = []
for feature in CHROMATIN_FEATURES:
    feature_path = BASE_LABEL_PATH / f"{feature}.tsv"
    
    print(f"Loading {feature_path}")
    labels = pd.read_csv(feature_path, header=None)[0].iloc[:len(merged_df)]

    assert len(labels) == len(merged_df), "Label length mismatch"

    label_dict[feature] = labels.values
    stats.append({
        "feature": feature,
        "positive": labels.sum(),
        "total": len(labels),
        "prevalence": labels.sum() / len(labels) 
    })

print("Merging with the Sequence Dataframes")
merged_df = merged_df.assign(**label_dict)

stats_df = pd.DataFrame(stats)
print(stats_df)

# Save the results
BASE_OUT_DIR = Path(args.output_dir)
BASE_OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Saving results to {BASE_OUT_DIR}")
for chrom in CHROMOSOMES:
    out_path = BASE_OUT_DIR / f"{chrom}.parquet"
    
    print(f"Saving {out_path}")
    merged_df[merged_df["chr"] == chrom].to_parquet(
        out_path,
        engine="pyarrow",
        compression="zstd",
        compression_level=3
    )

stats_path = BASE_OUT_DIR / "stats.tsv"
stats_df.to_csv(stats_path, sep="\t", index=False)
print(f"Saved stats to {stats_path}")