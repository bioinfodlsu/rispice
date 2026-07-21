import subprocess
from pathlib import Path

# HYPERPARAMETERS
CUTOFF_ANALYSIS = True

LEN = "200"   # default
GAP = "100"   # note that the bedGraphs are in 50bp bins

BDG_DIR = Path(".data2/prep/profiles/bdg")
OUTPUT_DIR = Path(".data2/prep/profiles/cutoff-analysis")
subdirectories = [x for x in BDG_DIR.iterdir() if x.is_dir()]

for directory in subdirectories:
    print(f"[Processing {directory.stem}]")
    files = [p for p in directory.iterdir() if p.is_file()]
    
    feature_dir = OUTPUT_DIR / directory.stem
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    for f in files:
        output_f = feature_dir / f"{f.stem}.narrowPeak"
        if CUTOFF_ANALYSIS:
            subprocess.run([
                "macs3", "bdgpeakcall",
                "-i", f, 
                "-o", output_f,
                "-l", LEN,
                "-g", GAP,
                "--cutoff-analysis"
                ])
        print(f"*Generated {output_f}")