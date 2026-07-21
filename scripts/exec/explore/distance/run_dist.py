import subprocess
from pathlib import Path

INPUT_BASE_DIR = Path("data/bed/distance/proposal")
OUTPUT_DIR = Path("analysis/explore/distance/proposal/dist")
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

for histone in HISTONE_MARKS:
    command = [
        "python", "-m", "scripts.explore.distance.dist",
        "-f", histone,
        "-d", INPUT_BASE_DIR / histone,
        "-o", OUTPUT_DIR
    ]
    subprocess.run(command, text=True, check=True)