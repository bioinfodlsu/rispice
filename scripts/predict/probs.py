import argparse
import torch
import numpy as np
import pandas as pd
from tqdm import tqdm
from ..constants import KMERS, MAX_LENGTH
from ..helper import get_features
from ..utils import PreTrainingUtils
from ..finetuning.train_utils import load_model
from peft import PeftModel
from pathlib import Path

from datasets import load_dataset
from torch.utils.data import DataLoader

def parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m scripts.predict.probs",
        description=(
            "Predict chromatin features for reference and alternate DNA sequences."
        )
    )

    parser.add_argument(
        "-m",
        "--model",
        required=True,
        help="Path to the RiSPICE base model directory.",
    )

    parser.add_argument(
        "-l",
        "--lora",
        help=(
            "Path to the RiSPICE LoRA adapter directory "
            "(e.g. 500 bp, 750 bp, or 1000 bp adapter)."
        )
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help=(
            "Input TSV file containing the generated reference and alternate "
            "sequences."
        ),
    )

    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where prediction results will be written.",
    )

    parser.add_argument(
        "-k",
        "--kmer",
        type=int,
        help=(
            "k-mer size for tokenization, if required by the selected model."
        ),
    )

    parser.add_argument(
        "--automodel",
        action="store_true",
        help="Load the model using Hugging Face AutoModel.",
    )

    parser.add_argument(
        "--cuda",
        action="store_true",
        help="Run inference on a CUDA-enabled GPU if available.",
    )

    parser.add_argument(
        "--features_path",
        default="features.csv",
        help=(
            "CSV file listing the chromatin features in the expected output "
            "order. (default: features.csv)"
        ),
    )

    return parser.parse_args()

def input_validation(args):
    # kmer
    if not args.kmer is None and not args.kmer in KMERS:
        raise Exception(f"{args.kmer}-mers are not supported. Should be in [3,4,5,6]")
    
    # model
    if not Path(args.model).exists():
        raise Exception(f"Model Path {args.model} not found.")
    
    # tokenizer
    if not Path(args.lora).exists():
        raise Exception(f"Lora Path {args.lora} not found.")
    
    # input
    if not Path(args.input).exists():
        raise Exception(f"Input Path {args.input} not found.")
    if not Path(args.input).is_file():
        raise Exception(f"Input Path {args.input} is not a file.")

def tokenize(sequences, tokenizer):
    return tokenizer(
        sequences,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
    )

def kmerize(sequences, k, max_kmers=MAX_LENGTH):
    return [
        PreTrainingUtils.kmerize(seq, k=k, max_kmers=max_kmers)
        for seq in sequences
    ]
    
def predict_and_save(model, tokenizer, tsv_path, column_name, out_path, batch_size=32, k=None):
    ds = load_dataset('csv', data_files=tsv_path, delimiter='\t', split='train')
    
    def transform(batch):
        return tokenizer(
            batch[column_name], 
            truncation=True, 
            padding="max_length", 
            max_length=MAX_LENGTH, 
            return_tensors="pt")
    
    def transform_k(batch, k):
        return tokenize(kmerize(batch, k), tokenizer)
        
    if k:
        ds.set_transform(transform_k)
    else:
        ds.set_transform(transform)
    
    loader = DataLoader(ds, batch_size=batch_size)
    
    model.eval()
    with open(out_path, 'w') as f:
        f.write("\t".join(FEATURES) + "\n")
        
        for batch in tqdm(loader, desc=f"Saving {column_name}"):
            inputs = {k: v.to(DEVICE) for k, v in batch.items()}
            with torch.inference_mode():
                outputs = model(**inputs)
                probs = torch.sigmoid(outputs.logits).cpu().numpy()
                
                # Append this batch directly to the file
                # index=False, header=False because we wrote the header above
                pd.DataFrame(probs).to_csv(f, sep="\t", index=False, header=False)

args = parse_args()
print(args)

FEATURES = get_features(args.features_path)
DEVICE = torch.device("cuda" if args.cuda else "cpu")

# Validate Input
input_validation(args)

model, tokenizer = load_model(args.model, args.automodel)

if args.lora:
    print(f"Loading adapters from {args.lora}")
    model = PeftModel.from_pretrained(model, args.lora)

model.to(DEVICE)

print(f"Loading Inputs at {args.input}")
print(f"Saving results to {args.output_dir}")
dir_path = Path(args.output_dir)
dir_path.mkdir(parents=True, exist_ok=True)

# ====== NEW STREAMING EXECUTION ========
ref_path = dir_path / "ref.tsv"
probs = predict_and_save(
    model=model,
    tokenizer=tokenizer,
    tsv_path=args.input,
    column_name="ref_seq",
    out_path=ref_path,
    k=args.kmer
)
print(f"Saved Ref Seq Predictions to {ref_path}")

alt_path = dir_path / "alt.tsv"
probs = predict_and_save(
    model=model,
    tokenizer=tokenizer,
    tsv_path=args.input,
    column_name="alt_seq",
    out_path=alt_path,
    k=args.kmer
)
print(f"Saved Alt Seq Predictions to {alt_path}")
