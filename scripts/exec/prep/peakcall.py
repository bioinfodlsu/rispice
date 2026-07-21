import subprocess
from pathlib import Path

# HYPERPARAMETERS
OCR_FEATURES = ["ATAC-Seq", "FAIRE-Seq"]
BROAD_FEATURES = ["H3K9me2", "H3K27me3", "H3K4me1", "H3K9me1"]


LEN = "200"   # default
GAP = "100"   # note that the bedGraphs are in 50bp bins

BDG_DIR = Path(".data2/prep/profiles/bdg")
OUTPUT_DIR = Path(".data2/prep/profiles/peaks")
subdirectories = [x for x in BDG_DIR.iterdir() if x.is_dir()]

for directory in subdirectories:
    print(f"[Processing {directory.stem}]")
    files = [p for p in directory.iterdir() if p.is_file()]
    
    feature_dir = OUTPUT_DIR / directory.stem
    feature_dir.mkdir(parents=True, exist_ok=True)

    # Sharp Marks
    if directory.stem not in BROAD_FEATURES:
        for f in files:
            output_f = feature_dir / f"{f.stem}.narrowPeak"
            
            subprocess.run([
                "macs3", "bdgpeakcall",
                "-i", f, 
                "-o", output_f
                ])
            print(f"*Used bdgpeakcall and generated {output_f}")
    else:
        for f in files:
            output_f = feature_dir / f"{f.stem}.bed"
            
            subprocess.run([
                "macs3", "bdgbroadcall",
                "-i", f, 
                "-o", output_f,
                "-g", GAP
                ])
            print(f"*Used bdgbroadcall and generated {output_f}")
            
            # Resolve blocks for enriched regions
            # block_f = feature_dir / f"{f.stem}.blocks.bed"
            # subprocess.run(
            #     f"bedtools bed12tobed6 -i {output_f} > {block_f}",
            #     shell=True,
            #     check=True
            # )
            # print(f"*Used bed12tobed6 and generated {block_f}")