import argparse, subprocess, os
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Execute tokenize script for all chromosomes")
    parser.add_argument(
        "-m",
        "--model",
        required=True,
        help="Path where the local model downloaded is stored"
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        help="Path where the datasets per chromosome are stored"
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Path where the resulting tokenized datasets would be stored"
    )
    return parser.parse_args()

def input_validation(args):
    # output path
    os.makedirs(args.output_dir, exist_ok=True)

args = parse_args()
print(args)

input_validation(args)

MODEL_PATH = args.model

# Tokenize
RAW_DIR = Path(args.input_dir)
RAW_PATHS = [p for p in RAW_DIR.iterdir() if p.is_dir()]

# Tokenize
TOKENIZED_DIR = Path(args.output_dir)
TOKENIZED_PATHS = [TOKENIZED_DIR / path.name for path in RAW_PATHS]

# Tokenize each training data
for index, _ in enumerate(RAW_PATHS):
    result = subprocess.run(
        [
            "python", "-u", "-m", "scripts.finetuning.tokenize",
            "-d", RAW_PATHS[index],
            "-o", TOKENIZED_PATHS[index],
            "-m", MODEL_PATH
        ],
        text=True,
        check=True
    )