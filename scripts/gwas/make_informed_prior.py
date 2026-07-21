import argparse
import pandas as pd
from scipy.special import softmax
from pathlib import Path

OPTIONS = ["norm", "softmax", "minmax"]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Given the Variant Scores, generate an informed prior for finemapping."
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
        "--output_dir",
        required=True,
        help="Path to the dir to where the output will be stored",
    )
    parser.add_argument(
        "--strategy",
        required=True,
        help="How the probabilities would be generated. (Options: norm, softmax, minmax)",
    )
    parser.add_argument(
        "--temp",
        type=float,
        default=0.2,
        help="Required for Minmax. (Default: 0.2)",
    )
    
    return parser.parse_args()

def linear_normalization(series: pd.Series) -> pd.Series:
    """Converts scores into a prior probability distribution

    where each value is proportional to its original score and the total sums to 1.
    """
    total = series.sum()

    # Edge case: If the sum is 0, distribute priors uniformly to avoid division by zero
    if total == 0:
        return pd.Series(1.0 / len(series), index=series.index)

    return series / total

def do_softmax(series: pd.Series) -> pd.Series:
    # scipy.special.softmax returns a numpy array; we wrap it back in a Series
    return pd.Series(softmax(series.values), index=series.index)

def do_minmax_softmax_with_temp(series: pd.Series, temperature: float = 1.0) -> pd.Series:
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return pd.Series(1.0 / len(series), index=series.index)

    # MinMax Scale
    minmax_scaled = (series - min_val) / (max_val - min_val)

    # Apply SciPy's softmax with temperature adjustment
    return pd.Series(
        softmax(minmax_scaled.values / temperature), index=series.index
    )

args = parse_args()
print(args)

if args.strategy not in OPTIONS:
    raise Exception(f"`--strategy` needs to be one of the ff: {str(OPTIONS)}")

# Extract and merge the snp list and scores
source = pd.concat([
        pd.read_csv(args.snp_list, sep="\t"),
        pd.read_csv(args.scores, sep="\t"),
    ], axis=1)

df = source[["chrom", "pos", "id", "Variant"]].copy()

print(f"Computing Prior with {args.strategy}")
# Compute Prior
if args.strategy == "norm":
    df.loc[:, "prior"] = linear_normalization(df["Variant"])
elif args.strategy == "softmax":
    df.loc[:, "prior"] = do_softmax(df["Variant"])
else:
    df.loc[:, "prior"] = do_minmax_softmax_with_temp(df["Variant"], args.temp)

# Save 
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

fn = "prior_" + args.strategy

if args.strategy == "minmax":
    fn += f"_{int(args.temp*100)}"

output_f = output_dir / f"{fn}.tsv"
df.to_csv(output_f, index=False, sep="\t")
print(f"Saved results to {output_f}")