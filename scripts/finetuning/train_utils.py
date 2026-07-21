import json, os
import numpy as np
from pathlib import Path
from datasets import load_from_disk
from transformers.trainer_utils import EvalLoopOutput, EvalPrediction
from transformers import (
    AutoModelForSequenceClassification,
    BertForSequenceClassification,
    TrainerCallback,
    DataCollatorWithPadding,
    AutoTokenizer,
    Trainer,
)

# torch
import torch
import torch.nn as nn
from torch.utils.data import IterableDataset
from tqdm import tqdm


class MemmapEvalTrainer(Trainer):
    def evaluation_loop(
        self,
        dataloader,
        description,
        prediction_loss_only=None,
        ignore_keys=None,
        metric_key_prefix="eval",
    ):
        model = self.model
        model.eval()

        device = self.args.device
        num_samples = len(dataloader.dataset)
        num_labels = model.config.num_labels

        loss_fct = nn.BCEWithLogitsLoss(reduction="sum")

        # Setup paths
        output_dir = Path(self.args.output_dir)
        checkpoint_dir = output_dir / f"checkpoint-{self.state.global_step}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logits_path = checkpoint_dir / "eval_logits.npy"
        labels_path = checkpoint_dir / "eval_labels.npy"

        # Setup memmaps
        logits_memmap = np.memmap(
            logits_path,
            mode="w+",
            dtype="float32",
            shape=(num_samples, num_labels),
        )

        labels_memmap = np.memmap(
            labels_path,
            mode="w+",
            dtype="float32",
            shape=(num_samples, num_labels),
        )

        # Train Loop
        total_loss = 0.0
        total_elements = 0
        idx = 0

        with torch.no_grad():
            for batch in tqdm(dataloader, desc=description):
                labels = batch["labels"].to(device)

                inputs = {k: v.to(device) for k, v in batch.items() if k != "labels"}

                outputs = model(**inputs)
                logits = outputs.logits

                # ----- compute BCE loss -----
                loss = loss_fct(logits, labels)

                total_loss += loss.item()
                total_elements += labels.numel()
                # --------------------------------

                bsz = logits.size(0)

                logits_memmap[idx : idx + bsz] = logits.cpu().numpy()
                labels_memmap[idx : idx + bsz] = labels.cpu().numpy()

                idx += bsz

        logits_memmap.flush()
        labels_memmap.flush()
        
        predictions = np.array(logits_memmap)
        labels_out = np.array(labels_memmap)
        
        del logits_memmap
        del labels_memmap

        # average loss per element (same as default Trainer)
        eval_loss = total_loss / total_elements

        # Compute metrics
        metrics = {f"{metric_key_prefix}_loss": eval_loss}
        
        if self.compute_metrics is not None:
            eval_pred = EvalPrediction(
                predictions=predictions,
                label_ids=labels_out
            )
            computed_metrics = self.compute_metrics(eval_pred)
            metrics.update(computed_metrics)

        return EvalLoopOutput(
            predictions=None,
            label_ids=None,
            metrics=metrics,
            num_samples=num_samples,
        )


class EvalLoggerCallback(TrainerCallback):
    def __init__(self, output_file):
        self.output_file = output_file

        # Check if Output File already exists (Resuming checkpoint)
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                self.records = json.load(f)
        else:
            self.records = []

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics is None:
            return

        record = {
            "step": state.global_step,
            "epoch": state.epoch,
            "eval_loss": metrics.get("eval_loss"),
        }

        for key, value in metrics.items():
            if key.startswith("eval_") and key != "eval_loss":
                record[key] = value

        self.records.append(record)

        with open(self.output_file, "w") as f:
            json.dump(self.records, f, indent=2)


class TrainingLoggerCallback(TrainerCallback):
    def __init__(self, output_file):
        self.output_file = output_file

        # Check if Output File already exists (Resuming checkpoint)
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                self.records = json.load(f)
        else:
            self.records = []

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return

        record = {"step": state.global_step, "epoch": state.epoch}
        for k, v in logs.items():
            if isinstance(v, (float, int)):
                record[k] = v
        self.records.append(record)
        with open(self.output_file, "w") as f:
            json.dump(self.records, f, indent=2)


class FloatLabelsCollator:
    def __init__(self, tokenizer):
        self.data_collator = DataCollatorWithPadding(tokenizer)

    def __call__(self, features):
        batch = self.data_collator(features)
        batch["labels"] = batch["labels"].float()
        return batch


class StreamingDataset(IterableDataset):
    def __init__(self, path):
        self.path = path

        # Load temporarily to get length, then discard
        temp_ds = load_from_disk(path)
        self.len = len(temp_ds)
        del temp_ds  # free memory

    def __iter__(self):
        ds = load_from_disk(self.path)
        for example in ds:
            yield example

    def __len__(self):
        """Return the total number of examples (needed by HuggingFace Trainer)."""
        return self.len


def compute_training_steps(
    num_samples: int,
    batch_size: int,
    num_epochs: int,
    grad_accum: int = 1,
    log_frac: float = 0.02,
    eval_frac: float = 0.10,
    min_logging_steps: int = 50,
    min_eval_steps: int = 200,
):
    """
    Compute Trainer step intervals strictly as fractions of an epoch.
    """
    assert grad_accum >= 1, "grad_accum must be >= 1"

    # Effective batch size is batch_size * grad_accum
    steps_per_epoch = int(np.ceil(num_samples / (batch_size * grad_accum)))
    total_steps = steps_per_epoch * num_epochs

    logging_steps = max(int(steps_per_epoch * log_frac), min_logging_steps)
    eval_steps = max(int(steps_per_epoch * eval_frac), min_eval_steps)

    return {
        "steps_per_epoch": steps_per_epoch,
        "total_steps": total_steps,
        "logging_steps": logging_steps,
        "eval_steps": eval_steps,
        "save_steps": eval_steps,
    }


def load_model(path, use_automodel=False):
    if not use_automodel:
        # Kmerized (DNABERT)
        model = BertForSequenceClassification.from_pretrained(
            path, problem_type="multi_label_classification"
        )
    else:
        # Non-kmerized
        model = AutoModelForSequenceClassification.from_pretrained(
            path, problem_type="multi_label_classification", trust_remote_code=True
        )

    tokenizer = AutoTokenizer.from_pretrained(path)
    return model, tokenizer


def count_model_params(model):
    """Utility function to count the total and trainable params of a model."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {
        "total": total,
        "trainable": trainable,
        "trainable_pct": 100 * trainable / total,
    }


def print_model_params(params, header):
    print(header)
    for k, v in params.items():
        if k != "trainable_pct":
            print(f"  {k}: {v:,}")
        else:
            print(f"  {k}: {round(v,2)}%")


def count_trainable_params(model):
    trainable = []
    for name, param in model.named_parameters():
        if param.requires_grad:
            trainable.append({"name": name, "value": param.numel()})

    return trainable


def print_trainable_params(params, header):
    print(header)
    for param in params:
        name = param["name"]
        parameters = param["value"]
        print(f"{name:60} | {parameters:>8}")
