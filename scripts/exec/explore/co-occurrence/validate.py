import pandas as pd
from pathlib import Path

BASE_IN_DIR = Path("analysis/explore/co-occurrence/proposal/chr")

# Initialize an empty DataFrame for accumulation
per_chrom_sum = None
per_ds_sum = None

for i in range(1,13):
    matrix = BASE_IN_DIR / f"{i}.tsv"
    
    df = pd.read_csv(matrix, sep="\t", index_col="Feature")
    
    if per_chrom_sum is None:
        per_chrom_sum = df.copy()
    else:
        per_chrom_sum += df  # element-wise addition
print(per_chrom_sum)


BASE_IN_DIR = Path("analysis/explore/co-occurrence/proposal")

for i in ["train", "test", "val"]:
    matrix = BASE_IN_DIR / f"{i}.tsv"
    
    df = pd.read_csv(matrix, sep="\t", index_col="Feature")
    
    if per_ds_sum is None:
        per_ds_sum = df.copy()
    else:
        per_ds_sum += df  # element-wise addition
     
print(per_ds_sum)

if per_chrom_sum.equals(per_ds_sum):
    print("Matrices are exactly equal")
else:
    print("Matrices differ")