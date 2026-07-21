import subprocess
from pathlib import Path

INPUT_PATH = Path("data/bed/distance/proposal/center")
HISTONE_MARKS = [
    "H3K23ac",
    "H4K16ac",
    "H3K4me3",
    "H3K36me3",
    "H3K27ac",
    "H3K9ac",
    "H4K12ac",
    "H3K27me3",
    "H3K4me1",
    "H3K9me2"
]

def computeClosest(a_feature, b_feature, output):
    command = f"bedtools closest -a {a_feature} -b {b_feature} -d -t first > {output}"
    subprocess.run(command, shell=True, check=True)

for feature in HISTONE_MARKS:
    output_path = Path(f"data/bed/distance/proposal/{feature}")
    output_path.mkdir(parents=True, exist_ok=True)
    a = INPUT_PATH / f"{feature}_center.bed"
    
    print(f"\nComputing Closest for {a}")
    for histone in HISTONE_MARKS:
        # Skip if histone is the feature
        if histone == feature:
            continue
        
        b = INPUT_PATH / f"{histone}_center.bed"
        output_file = output_path / f"vs_{histone}.tsv"
        
        print(f"Processing {b}")
        computeClosest(a, b, output_file)
        print(f"Saved {output_file}")
