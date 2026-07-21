import argparse, subprocess
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Execute run_tokenizer for all datasets (train, test, val)")
    # parser.add_argument(
    #     "-k",
    #     "--kmer",
    #     help="Kmer dataset to execute run_tokenizer.py for."
    # )
    # parser.add_argument(
    #     "-u",
    #     "--uid",
    #     required=True,
    #     help="The specific key where the results for each phase of the process will be stored."
    # )
    # parser.add_argument(
    #     "--model_key",
    #     help="Key to be appended distinguishing this model from others"
    # )
    # parser.add_argument(
    #     "-m",
    #     "--model_path",
    #     help="Path to the model"
    # )
    parser.add_argument(
        "-i",
        "--input_dir",
        help="input_dir."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="output_dir."
    )
    return parser.parse_args()

args = parse_args()
print(args)

# MODEL_PATH = Path(args.model_path)
BASE_IN_PATH = Path(args.input_dir)
BASE_OUT_PATH = Path(args.output_dir)

# if not args.model_key is None:
#     model_key = args.model_key
#     path_key = args.model_key
# else:
#     model_key = f"{args.kmer}mer"
#     path_key = f"k{args.kmer}"

# MODEL_PATH = Path(f"models/base/{model_key}")
# BASE_IN_PATH = Path(f"data/finetune/histone/tokenized/{args.uid}/{path_key}")
# BASE_OUT_PATH = Path(f"data/finetune/histone/final/{args.uid}/{path_key}")

script_name = "scripts.finetuning.concat_datasets"
for ds in ["train", "test", "val"]:
    input_path = BASE_IN_PATH / ds
    output_path = BASE_OUT_PATH
    
    print(input_path)
    print(output_path)
    
    print(f"[START] Processing {ds}")
    subprocess.run([
        "python", "-m", script_name,
        "-i", input_path,
        "-o", output_path,
        "-n", ds
    ])
    print(f"[END]Finished {ds}")