import argparse, subprocess
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Execute kmerize_ds script for all chromosomes")
    parser.add_argument(
        "-k",
        "--kmer",
        required=True,
        help="The kmer to be used when executing the kmerize_ds script"
    )
    parser.add_argument(
        "-u",
        "--uid",
        default="stratified",
        help="The specific key where the results for each phase of the process will be stored."
    )
    return parser.parse_args()

def exec_kmerize_ds(input_path, kmer, output_path):
    module_name = "scripts.finetuning.kmerize_ds"
    print(f"[START] Processing {input_path}")
    subprocess.run([
        "python", "-m", module_name,
        "-i", input_path,
        "-o", output_path,
        "-k", kmer
    ])
    print(f"[END]Finished {input_path}")

def iterate_exec(input_paths, output_paths, kmer):
    for i in range(len(input_paths)):
        exec_kmerize_ds(
            input_path=input_paths[i],
            output_path=output_paths[i],
            kmer=kmer
        )

def prep(ds_type, kmer, uid):
    """Prepare necessary info. ds_type param is either train, test, or val."""
    base_input_path = Path(f"data/finetune/histone/raw/{uid}/{ds_type}")
    base_output_path = Path(f"data/finetune/histone/kmerized/{uid}/k{kmer}/{ds_type}")
    
    input_paths = []
    output_paths = []
    for p in base_input_path.iterdir():
        if p.is_dir():
            input_paths.append(p)
            output_paths.append(base_output_path / p.name)
    
    return input_paths, output_paths
    

args = parse_args()
print(args)

# Setup input paths
print("Prepping input and output paths...")
in_train, out_train = prep("train", args.kmer, args.uid)
in_test, out_test = prep("test", args.kmer, args.uid)
in_val, out_val = prep("val", args.kmer, args.uid)

# Execute train
print("Executing Train Datasets...")
iterate_exec(in_train, out_train, args.kmer)

# Execute test
print("Executing Test Datasets...")
iterate_exec(in_test, out_test, args.kmer)

# Execute val
print("Executing Val Datasets...")
iterate_exec(in_val, out_val, args.kmer)


