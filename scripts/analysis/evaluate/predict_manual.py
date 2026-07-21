import argparse
import numpy as np
from ...finetuning.train_utils import load_model
from ...helper import get_features
from peft import PeftModel
from datasets import load_from_disk
from pathlib import Path
from tqdm import tqdm

# torch
import torch
from torch.utils.data import DataLoader


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute for the logits and labels of a trained (LoRA) model. Non-HF Version."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Directory where the results would be stored.",
    )
    parser.add_argument(
        "-m",
        "--model",
        required=True,
        help="Directory of the base model used during training.",
    )
    parser.add_argument(
        "-l",
        "--lora",
        help="Directory of the trained lora adapter during training.",
    )
    parser.add_argument(
        "-d",
        "--dataset",
        help="Dataset to be used for evaluating the model.",
    )
    
    
    parser.add_argument("--automodel", action="store_true")
    
    # Hyperparams
    # parser.add_argument("--label_cnt", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--num_of_workers", type=int, default=4)
    
    parser.add_argument(
        "--features_path",
        default=".data2/prep/constant/features.csv",
        help="Path to csv file containing the list of all features to process (ensure sorting.).",
    )
    
    return parser.parse_args()

args = parse_args()
print(args)

FEATURES = get_features(args.features_path)

# Load the models
print(f"Loading model from {args.model}")
model, tokenizer = load_model(args.model, args.automodel)

if args.lora:
    print(f"Loading adapters from {args.lora}")
    model = PeftModel.from_pretrained(model, args.lora)

model.eval()

# Load the dataset
print(f"Loading dataset from {args.dataset}")
ds = load_from_disk(args.dataset)
ds = ds.remove_columns(["seq"])     # Remove the Seq
print(f"Loaded with {len(ds)} samples")

# setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)    # transfer to GPU
print(f"Transferred model to {device}")

# convert huggingface to torch
print(f"Converting dataset to `torch` format")
ds.set_format(type="torch")
print(ds)
dataloader = DataLoader(
    ds,
    batch_size=args.batch_size,
    shuffle=False,
    num_workers=args.num_of_workers
)

N = len(ds)
num_outputs = len(FEATURES)     # Predicted Labels
print((N, num_outputs))

# Make output dir
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

# Allocate memmaps
logits_path = output_dir / "logits.npy"
labels_path = output_dir / "labels.npy"

print(f"Preparing logits memmap to {logits_path}")
print(f"Preparing labels memmap to {labels_path}")
logits_memmap = np.lib.format.open_memmap(
    logits_path,
    mode="w+",
    dtype="float32",
    shape=(N, num_outputs)
)

labels_memmap = np.lib.format.open_memmap(
    labels_path,
    mode="w+",
    dtype="float32",   # change to int64 if needed
    shape=(N, num_outputs)
)

print("Evaluating...")
idx = 0
with torch.no_grad():
    for batch in tqdm(dataloader):
        labels = batch["labels"]
        inputs = {
            k: v.to(device)
            for k, v in batch.items()
            if k not in ["labels", "seq"]
        }

        outputs = model(**inputs)
        logits = outputs.logits

        bsz = logits.size(0)

        logits_memmap[idx:idx+bsz] = logits.cpu().numpy()
        labels_memmap[idx:idx+bsz] = labels.cpu().numpy()

        idx += bsz

logits_memmap.flush()
labels_memmap.flush()