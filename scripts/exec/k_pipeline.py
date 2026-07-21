import argparse, subprocess
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Execute pipeline for a specific K (kmerize -> tokenize -> finalize).")
    parser.add_argument(
        "-k",
        "--kmer",
        help="Kmer dataset to execute the pipeline for."
    )
    parser.add_argument(
        "-u",
        "--uid",
        required=True,
        help="The specific key where the results for each phase of the process will be stored."
    )
    parser.add_argument(
        "--subsample",
        action="store_true",
        help="Kmer dataset to execute run_tokenizer.py for."
    )
    parser.add_argument(
        "--subsample_grp_name",
        default="toy",
    )
    parser.add_argument(
        "--train_cnt",
        type=int,
        default=10000,
    )
    parser.add_argument(
        "--val_cnt",
        type=int,
        default=2000,
    )
    parser.add_argument(
        "--delete_tokenized",
        action="store_true",
        help="Delete the created tokenized folder after execution."
    )
    parser.add_argument(
        "--model_key",
        help="Specify specific key needed if kmerization is skipped."
    )
    return parser.parse_args()

def delete_dir(path):
    subprocess.run([
        "rm", "-rf", path
    ])

def execute_script(script_name, k, uid, model_key=None, prev_stage="raw"):
    if model_key is None:
        subprocess.run([
            "python", script_name,
            "--kmer", k,
            "--uid", uid,
        ])
    else:
        subprocess.run([
            "python", script_name,
            "--model_key", model_key,
            "--uid", uid,
            "--prev_stage", 
        ])

def exec_script_k(script_name, k, uid):
    subprocess.run([
            "python", script_name,
            "--kmer", k,
            "--uid", uid,
    ])
    
def exec_script_others(script_name, model_key, uid, prev_stage=None):
    if prev_stage is None:
        subprocess.run([
            "python", script_name,
            "--model_key", model_key,
            "--uid", uid,
        ])
    else:
        subprocess.run([
            "python", script_name,
            "--model_key", model_key,
            "--uid", uid,
            "--prev_stage", prev_stage
        ])
    

def subsample(k, ds, count, grp_name):
    input_dir = Path(f"data/finetune/histone/tokenized/stratified/k{k}/{ds}")
    output_dir = Path(f"data/finetune/histone/final/{grp_name}/k{k}")

    subprocess.run([
        "python", "-m", "scripts.finetuning.subsample_ds",
        "-i", input_dir,
        "-o", output_dir,
        "-n", ds,
        "--count", str(count),
        "--save"
    ])

KMERIZED_PATH = Path("data/finetune/histone/kmerized")
TOKENIZED_PATH = Path("data/finetune/histone/tokenized")

KMERIZE_SCRIPT = Path("scripts/exec/run_kmerize_ds.py")
TOKENIZE_SCRIPT = Path("scripts/exec/batch_tokenize.py")
CONCAT_SCRIPT = Path("scripts/exec/batch_concat_ds.py")

args = parse_args()
print(args)

# Execute kmerize
if args.kmer:
    print(f"[PIPELINE][K={args.kmer}] Kmerizing dataset via {KMERIZE_SCRIPT}")
    exec_script_k("scripts/exec/run_kmerize_ds.py", args.kmer, args.uid)

# Execute tokenize
print(f"[PIPELINE][K={args.kmer}] Tokenizing dataset via {TOKENIZE_SCRIPT}")
if args.kmer:
    exec_script_k("scripts/exec/batch_tokenize.py", args.kmer, args.uid)
else:
    exec_script_others("scripts/exec/batch_tokenize.py", args.model_key, args.uid, "raw")

# Delete kmerize
if args.kmer:
    print(f"[PIPELINE][K={args.kmer}] Deleting kmerized dir")
    delete_dir(KMERIZED_PATH)

# Execute concat
# Check if count is given
if args.subsample:
    print(f"[PIPELINE][K={args.kmer}] Processing subsample (10000 train, 2000 val)")
    subsample(k=args.kmer, ds="train", count=args.train_cnt, grp_name=args.subsample_grp_name)
    subsample(k=args.kmer, ds="val", count=args.val_cnt, grp_name=args.subsample_grp_name)
else:
    if args.kmer:
        print(f"[PIPELINE][K={args.kmer}] Processing complete dataset")
        exec_script_k("scripts/exec/batch_concat_ds.py", args.kmer, args.uid)
    else:
        print(f"[PIPELINE][{args.model_key}] Processing complete dataset")
        exec_script_others("scripts/exec/batch_concat_ds.py", args.model_key, args.uid)

# Delete tokenized
if args.delete_tokenized:
    print(f"[PIPELINE] Deleting tokenized dir {TOKENIZED_PATH}")
    delete_dir(TOKENIZED_PATH)