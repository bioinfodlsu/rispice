import argparse, subprocess
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize AUROC for All KMER DNABERT Models"
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Directory containing all kmer_models",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where all the outputs would be placed",
    )
    return parser.parse_args()

def validate_path_exists(path):
    for k in [3,4,5,6]:
        k_path = path / f"k{k}"
        
        if not k_path.exists():
            raise FileNotFoundError(f"Path for model does not exist: {k_path}")

args = parse_args()
print(args)

BASE_INPUT = Path(args.input_dir)
BASE_OUTPUT = Path(args.output_dir)

validate_path_exists(BASE_INPUT)

# Process each k
for k in [3,4,5,6]:
    input_file = BASE_INPUT / f"k{k}" / f"eval_metrics.json"
    output_fn = f"k{k}"
    
    module = "scripts.analysis.visualize.training.per_threshold_step"
    metric_key = "recall_macro"
    
    key_label = "Recall (Macro)"
    graph_title = f"Macro Recall Per Threshold for DNABERT (K={k})"
    print(f"[START K={k}] Processing {input_file}")
    subprocess.run([
        "python", "-m", module,
        "-i", input_file,
        "--key", metric_key,
        "--key_label", key_label,
        "--title", graph_title,
        "--output_dir", BASE_OUTPUT,
        "--output_fn", f"k{k}",
    ])
    
    output = BASE_OUTPUT / f"k{k}.png"
    print(f"[END K={k}] Generated {output}")
