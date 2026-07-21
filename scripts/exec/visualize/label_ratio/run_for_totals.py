import subprocess, pandas as pd
from pathlib import Path

SEQ_LEN = "1000"
BASE_TOTAL_DIR = Path(f"analysis2/prevalence/{SEQ_LEN}")
BASE_OUT_DIR = Path(f"figures2/prevalence/{SEQ_LEN}")

COLUMN_FILE = Path("data/histone/constant/histone_marks.csv")

def execute_script(input_file, graph_title, module_name):
    print(f"[START] Processing {input_file}")
    subprocess.run([
        "python", "-m", module_name,
        "-f", input_file,
        "-o", BASE_OUT_DIR,
        "--graph_title", graph_title
    ])
    print(f"[END]Finished {input_file}")

# Find Ratios Per Chromosome Across the Genome
input_file = BASE_TOTAL_DIR / "per_chrom.csv"
graph_title = "Prevalence per Chromosome (Across the Genome)"
module = "scripts.analysis.visualize.label_ratio.per_mark_stacked_bar"
execute_script(input_file, graph_title, module)

# Find Ratios Per Chromosome Across the Genome
input_file = BASE_TOTAL_DIR / "per_mark.csv"
graph_title = "Prevalence per Chromatin Feature (Across the Genome)"
module = "scripts.analysis.visualize.label_ratio.per_chrom_stacked_bar"
execute_script(input_file, graph_title, module)

# For Per_Chrom_Grouped_Bar, it might not be viable to reuse for the total due to different scaling
# TODO: Make a separate script for that one, mirroring the per_chrom_grouped_bar