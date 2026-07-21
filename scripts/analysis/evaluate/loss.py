import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute for the ROC and PRC curves given logits and labels."
    )
    parser.add_argument(
        "--logits",
        required=True,
        help="logits .npy file.",
    )
    parser.add_argument(
        "--labels",
        required=True,
        help="labels .npy file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="tsv file containing the results.",
    )

    return parser.parse_args()

args = parse_args()
print(args)

print(f"Loading logits from {args.logits}")
logits = np.load(args.logits)

print(f"Loading labels from {args.labels}")
labels = np.load(args.labels)

# Convert to tensors
print(f"Converting to tensors")
logits = torch.tensor(logits, dtype=torch.float32)
labels = torch.tensor(labels, dtype=torch.float32)

print("Computing BCE with Logits Loss")
loss = F.binary_cross_entropy_with_logits(logits, labels)
print(loss.item())

df = pd.DataFrame({
    "metric": ["bce_with_logits_loss"],
    "value": [loss.item()]
})

# Save Results
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output, sep="\t", index=False)
print(f"Saved results to {output}")
