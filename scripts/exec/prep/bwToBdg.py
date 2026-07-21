import subprocess
from pathlib import Path

RICE_ENCODE_DIR = Path(".data/RiceENCODE/Histone")
OUTPUT_DIR = Path(".data2/prep/profiles/bdg")
subdirectories = [x for x in RICE_ENCODE_DIR.iterdir() if x.is_dir()]

for directory in subdirectories:
    print(f"[Processing {directory.stem}]")
    files = [p for p in directory.iterdir() if p.is_file()]
    
    feature_dir = OUTPUT_DIR / directory.stem
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    for f in files:
        output_f = feature_dir / f"{f.stem}.bedGraph"
        subprocess.run([
            "scripts/uscs/bigWigToBedGraph", f, output_f])
        print(f"*Generated {output_f}")