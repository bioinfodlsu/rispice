import argparse
import pandas as pd
import numpy as np
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Perform multitesting via adjusted M_eff and Benjamin-Hochberg."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the p-values file.",
    )
    parser.add_argument(
        "--ld",
        required=True,
        help=".ld file of the snps generated via PLINK.",
    )
    parser.add_argument(
        "-q",
        "--q_value",
        default=0.05,
        type=float,
        help="The alpha value.",
    )
    parser.add_argument(
        "--method",
        required=True,
        help="The method to perform (Options: `bh`, `bonf`, `sidak`, `bh_meff`).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path where the file will be saved to.",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="If flagged, it will not save the output to the file"
    )
    
    return parser.parse_args()

def compute_effective_m(ld_matrix):
    M = len(ld_matrix)
    eigenvalues = np.linalg.eigvalsh(ld_matrix)
    
    # Take absolute values of eigenvals |lambda|
    x = np.abs(eigenvalues)
    
    # f(x) = I(x >= 1) + (x - floor(x))
    f_x = (x >= 1).astype(int) + (x - np.floor(x))
    
    m_eff_raw = np.sum(f_x)
    m_eff = max(1, int(np.round(m_eff_raw)))
    
    print(f"-> Effective independent tests (M_eff): {m_eff}")
    return m_eff

def bh(input_df, q, m, p_col="p-value"):
    df = input_df.copy()
    df.sort_values(by=p_col, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Rank p-values
    df["rank"] = df.index + 1
    
    # Compute the formal BH threshold: (k / m) * q
    df["bh_threshold"] = (df["rank"] / m) * q
    
    # Find the indexes where the condition P_(k) <= (k / m) * q is satisfied
    sig_indexes = df[df['p-value'] <= df['bh_threshold']].index
    
    if len(sig_indexes) > 0:
        # The largest index (highest rank k) that met the criteria
        max_sig_idx = sig_indexes.max()
        
        # Mark everything up to (and including) this index as significant
        df['significant'] = df.index <= max_sig_idx
    else:
        df['significant'] = False
    
    print(f"Number of SNPs that survived BH: {np.sum(df['significant'] )}")
    return df, None # there's no adjusted alpha

def bh_meff(input_df, q, m_eff, p_col="p-value"):
    """
    Modified Benjamini-Hochberg (step-up) procedure incorporating the 
    effective number of independent tests (M_eff) to account for correlation.
    """
    df = input_df.copy()
    df.sort_values(by=p_col, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Rank p-values
    df["rank"] = df.index + 1
    
    # =========================================================================
    # FORMULA ANNOTATION:
    # Threshold = [q / M_eff] + [ (i - 1) / (M - 1) ] * [ q - (q / M_eff) ]
    #
    #   * q / m_eff       : The starting value of the sequence (EWSL threshold)
    #   * (i-1) / (m-1)   : The step coefficient scale (0 when i=1, 1 when i=M)
    #   * q               : The final controlled FDR rate at the end of the sequence
    #   * q - (q / m_eff) : The overall span/range of the sequence
    # =========================================================================
    start_term = q / m_eff
    step_multiplier = (df["rank"] - 1) / (len(df) - 1)
    span_term = q - (q / m_eff)
    
    # Compute the formal Meff-based threshold
    df["bh_threshold"] = start_term + (step_multiplier * span_term)
    
    # Find the indexes where the condition P_(k) <= (k / m) * q is satisfied
    sig_indexes = df[df[p_col] <= df['bh_threshold']].index
    
    if len(sig_indexes) > 0:
        # The largest index (highest rank k) that met the criteria
        max_sig_idx = sig_indexes.max()
        
        # Reject H_(1), ..., H_(k) (mark everything up to and including 'k' as significant)
        df['significant'] = df.index <= max_sig_idx
    else:
        df['significant'] = False
    
    print(f"Number of SNPs that survived BH_Meff: {np.sum(df['significant'] )}")
    return df, None # there's no adjusted alpha

def bonferroni(input_df, q, m, p_col="p-value"):
    df = input_df.copy()
    
    # Bonferroni formula for adjusted alpha
    adjusted_alpha = q / m
    
    # Compute adjusted-p for ref
    df["p_bonferroni"] = df[p_col] * m
    df["p_bonferroni"] = np.minimum(df["p_bonferroni"], 1.0)
    
    # Check significance based on adjusted alpha
    df["significant"] = df[p_col] <= adjusted_alpha
    
    print(f"Adjusted Alpha (from {q}): {adjusted_alpha}")
    print(f"Number of SNPs that survived Adjusted Bonferroni: {np.sum(df['significant'] )}")
    return df, adjusted_alpha

def sidak(input_df, q, m, p_col="p-value"):
    df = input_df.copy()
    
    # Sidak formula for adjusted alpha
    adjusted_alpha = 1 - (1 - q) ** (1/m)
    
    # Compute adjusted-p for ref
    df["p_sidak"] = 1 - (1 - df[p_col]) ** m
    
    # Check significance based on adjusted alpha
    df["significant"] = df[p_col] <= adjusted_alpha
    
    print(f"Adjusted Alpha (from {q}): {adjusted_alpha}")
    print(f"Number of SNPs that survived Adjusted Sidak: {np.sum(df['significant'] )}")
    return df, adjusted_alpha

args = parse_args()
print(args)

# Read the data
ld_matrix = pd.read_csv(args.ld, sep=r"\s+", header=None, index_col=False).to_numpy()
df = pd.read_csv(args.input, sep="\t")

print(f"M = {len(ld_matrix)}")

assert (
    ld_matrix.shape[0] == len(df)
), f"Dimension mismatch! Matrix: {ld_matrix.shape[0]}, Scores: {len(df)}"

# Compute for M_eff
m_eff = compute_effective_m(ld_matrix)

if args.method == "bh":
    results, adjusted_alpha = bh(df, args.q_value, m_eff)
elif args.method == "bh_meff":
    results, adjusted_alpha = bh_meff(df, args.q_value, m_eff)
elif args.method == "bonf":
    results, adjusted_alpha = bonferroni(df, args.q_value, m_eff)
elif args.method == "sidak":
    results, adjusted_alpha = sidak(df, args.q_value, m_eff)
else:
    raise ValueError(f"method should be one of `bh`, `bonf`, `sidak`.")

print(results.head())

# Save to file
if not args.test:
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write(f"## Input: {args.input}\n")
        f.write(f"## LD: {args.ld}\n")
        f.write(f"## M: {len(ld_matrix)}\n")
        f.write(f"## Q: {args.q_value}\n")
        f.write(f"## Method: {args.method}\n")
        f.write(f"## M_eff: {m_eff}\n")
        
        if adjusted_alpha:
            f.write(f"## Adjusted Q: {adjusted_alpha}\n")
            
        results.to_csv(f, sep="\t", index=False)
        print(f"File successfully saved to: {output_file}")