import argparse, os
from datasets import load_from_disk
from transformers import AutoTokenizer
from ..constants import MAX_LENGTH
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Tokenize a Dataset")
    parser.add_argument(
        "-d",
        "--dataset",
        required=True,
        help="Path to Dataset.",
    )
    parser.add_argument(
        "-f",
        "--feature_key",
        default="seq",
        help="Key within the Dataset to be tokenized. (Default: 'seq')",
    )
    parser.add_argument(
        "-m",
        "--model",
        required=True,
        help="The path to the model that has been saved locally. Requires following HuggingFace standard.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where the tokenized dataset will be placed.",
    )

    args = parser.parse_args()
    return args


def input_validation(args):
    # output path
    os.makedirs(args.output_dir, exist_ok=True)


def tokenize_fn(data, key):
    return tokenizer(
        data[key],
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
    )


args = parse_args()
print(args)

input_validation(args)

# Load the dataset
ds = load_from_disk(args.dataset)

# Perform Tokenization
try:
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    print(f"Tokenizer loaded successfully from {args.model}")

    # tokenize
    tok_ds = ds.map(tokenize_fn, fn_kwargs={"key": args.feature_key}, batched=True)
    
    # Save dataset
    tok_ds.save_to_disk(args.output_dir)
    print(f"Saved tokenized dataset to {args.output_dir}")

except OSError as e:
    print(f"Error loading tokenizer: {e}")
