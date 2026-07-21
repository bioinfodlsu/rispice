import argparse, numpy as np
from ...finetuning.train_utils import load_model, FloatLabelsCollator
from peft import PeftModel
from datasets import load_from_disk
from transformers import Trainer, TrainingArguments
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute for the logits and labels of a trained (LoRA) model."
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
    
    parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="batch_size during evaluation.",
    )
    parser.add_argument("--dataloader_num_workers", type=int, default=4)
    parser.add_argument("--eval_accumulation_steps", type=int, default=5)
    parser.add_argument("--automodel", action="store_true")
    
    return parser.parse_args()

args = parse_args()
print(args)

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

# Setup the Trainer
training_args = TrainingArguments(
    output_dir="./tmp",
    per_device_eval_batch_size=args.batch_size,
    dataloader_num_workers=args.dataloader_num_workers,
    eval_accumulation_steps=args.eval_accumulation_steps
)

trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=FloatLabelsCollator(tokenizer)
)


# Predict
print(f"Processing predictions...")
predictions = trainer.predict(ds)

# Extract logits and labels
logits = predictions.predictions  # shape: (num_samples, num_classes)
labels = predictions.label_ids    # shape: (num_samples,) if available

# Save to file
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

logits_path = output_dir / "logits.npy"
np.save(logits_path, logits)
print(f"Saved logits to {logits_path}")

if labels is not None:
    labels_path = output_dir / "labels.npy"
    np.save(labels_path, labels)
    print(f"Saved labels to {labels_path}")