import argparse, pandas as pd
from pathlib import Path
from ...constants import BASES

def parse_args():
    parser = argparse.ArgumentParser(
        description="Process the Scores of the Variants for Mutagenesis Analysis."
    )
    parser.add_argument(
        "--scores",
        required=True,
        help="Path to the scores.tsv file.",
    )
    parser.add_argument(
        "--snp_list",
        required=True,
        help="Path to the snp_list.tsv file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Save the results to the file",
    )
    parser.add_argument(
        "--metric",
        default="Variant",
        help="The metric that would be used for sorting the variants. (Default: Variant)",
    )
    
    return parser.parse_args()

def get_ref_seq(df) -> str:
    df = df[df["alt"] == "A"]
    return df["ref"].tolist()

def get_ids(df) -> str:
    df = df[df["alt"] == "A"]
    temp = "Chr" + df["chrom"].astype(str) + ":" + df["pos"].astype(str)
    return temp.tolist()

args = parse_args()
print(args)

# Extract and merge the snp list and scores
df = pd.concat([
        pd.read_csv(args.snp_list, sep="\t"),
        pd.read_csv(args.scores, sep="\t"),
    ], axis=1)


# Get the Scores Per Base
mutagenesis_df = pd.DataFrame({
        "id": get_ids(df),
        "ref": get_ref_seq(df) # Get Reference Sequence
    }) 

# Get the Scores Per ALT Base
for base in BASES:
    mutagenesis_df[base] = df[df["alt"] == base].reset_index()[args.metric]

# Get the Cumulative Score
mutagenesis_df["cumulative"] = mutagenesis_df["A"] + mutagenesis_df["C"] + mutagenesis_df["G"] + mutagenesis_df["T"]

# Get the Max Effect
mutagenesis_df["max_effect"] = mutagenesis_df[BASES].abs().max(axis=1)
print(mutagenesis_df)

# Setup output_dir
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

mutagenesis_df.to_csv(output_path, sep="\t", index=False)
print(f"Saved Mutagenesis Analysis Matrix to {output_path}")