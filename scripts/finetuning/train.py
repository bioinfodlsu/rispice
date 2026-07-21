import argparse, os, json
import numpy as np
from transformers import (
    BertForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    AutoModelForSequenceClassification
)
from datasets import load_from_disk
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
)
from pathlib import Path
from scipy.special import expit
from transformers import EarlyStoppingCallback
from .train_utils import (
    EvalLoggerCallback,
    TrainingLoggerCallback,
    FloatLabelsCollator,
    count_model_params,
    print_model_params,
    count_trainable_params,
    MemmapEvalTrainer
)
from ..helper import get_features
from transformers.trainer_utils import get_last_checkpoint
from peft import LoraConfig, TaskType, get_peft_model

def parse_args():
    parser = argparse.ArgumentParser(
        description="Train DNABERT for multilabel histone mark prediction"
    )
    parser.add_argument(
        "--train_params",
        required=True,
        help="JSON File containing all the parameters for training. Generated through make_param_file.py",
    )
    parser.add_argument(
        "--lora_params",
        help="JSON File containing all the parameters for training. Generated through make_param_file.py",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Output directory",
    )
    
    parser.add_argument(
        "--use_automodel",
        action="store_true",
        help="When loading the model, use AutoModelForSequenceClassification.",
    )
    parser.add_argument(
        "--prediction_loss_only",
        action="store_true",
        help="During training, only keep track of the prediction loss.",
    )

    parser.add_argument(
        "--features_path",
        default=".data2/prep/constant/features.csv",
        help="Path to csv file containing the list of all features to process (ensure sorting.).",
    )
    
    return parser.parse_args()


def per_label_metrics(labels, probs, label_names):
    """
    labels: shape (N,)
    probs:  shape (N, C)
    """
    metrics = {}

    try:
        auroc_per_label = roc_auc_score(labels, probs, average=None, multi_class="ovr")
        auprc_per_label = average_precision_score(labels, probs, average=None)

        for i in range(len(auroc_per_label)):
            name = label_names[i] if label_names else f"class_{i}"
            metrics[f"auroc_{name}"] = auroc_per_label[i]
            metrics[f"auprc_{name}"] = auprc_per_label[i]

    except ValueError:
        # Happens if a class has no positives
        for i in range(probs.shape[1]):
            name = label_names[i] if label_names else f"class_{i}"
            metrics[f"auroc_{name}"] = np.nan
            metrics[f"auprc_{name}"] = np.nan

    return metrics


def compute_metrics(eval_pred):
    # Checking incase prediction_loss_only is setup
    if eval_pred.predictions is None:
        return {}
    
    logits = eval_pred.predictions
    labels = eval_pred.label_ids
    labels = labels.astype(int)
    probs = expit(logits)

    metrics = {}

    try:
        metrics["auprc_macro"] = average_precision_score(labels, probs, average="macro")
        metrics["auroc_macro"] = roc_auc_score(labels, probs, average="macro")

        # micro metrics (flatten all labels)
        metrics["auprc_micro"] = average_precision_score(
            labels.reshape(-1), probs.reshape(-1)
        )
        metrics["auroc_micro"] = roc_auc_score(labels.reshape(-1), probs.reshape(-1))

        metrics["micro_auprc_baseline"] = float(labels.mean())

    except ValueError:
        metrics["auprc_macro"] = np.nan
        metrics["auroc_macro"] = np.nan
        metrics["auprc_micro"] = np.nan
        metrics["auroc_micro"] = np.nan

    # per-label metrics
    metrics.update(per_label_metrics(labels, probs, label_names=FEATURES))

    return metrics


def load_model(path, use_automodel=False):
    if not use_automodel:
        # Kmerized (DNABERT)
        model = BertForSequenceClassification.from_pretrained(
            path, problem_type="multi_label_classification"
        )
    else:
        # Non-kmerized
        model = AutoModelForSequenceClassification.from_pretrained(
            path,
            problem_type="multi_label_classification",
            trust_remote_code=True
        )
    
    tokenizer = AutoTokenizer.from_pretrained(path)
    return model, tokenizer

def load_params(params_path):
    with open(params_path, "r") as f:
        params = json.load(f)
    return params

def save_params(params_path, params):
    with open(params_path, "w") as f:
        json.dump(params, f, indent=2)
    print(f"Saved parameters to {params_path}")

def setup_training_args(train_params, checkpoint_dir, keep_pred_loss_only=False):
    """Using Training Params, instantiate a `TrainingArguments` object"""
    return TrainingArguments(
        output_dir=train_params["output_dir"],
        # Strategy
        eval_strategy="steps",
        save_strategy="steps",
        logging_strategy="steps",
        # Steps
        logging_steps=train_params["logging_steps"],
        eval_steps=train_params["eval_steps"],
        save_steps=train_params["save_steps"],
        # Hyperparams
        learning_rate=train_params["learning_rate"],
        num_train_epochs=train_params["epoch"],
        weight_decay=train_params["weight_decay"],
        # Minimal logging
        log_level="error",
        logging_first_step=True,
        report_to=[],
        # Checkpoint control
        resume_from_checkpoint=checkpoint_dir,
        save_total_limit=train_params["save_total_limit"],
        load_best_model_at_end=True,
        metric_for_best_model=train_params["metric_for_best_model"],
        greater_is_better=train_params["greater_is_better"],
        # Performance
        fp16=True,
        dataloader_num_workers=train_params["dataloader_num_workers"],
        eval_accumulation_steps=train_params["eval_accumulation_steps"],
        per_device_train_batch_size=train_params["batch_size"],
        per_device_eval_batch_size=train_params["eval_batch_size"],
        
        gradient_accumulation_steps=train_params["grad_accum"],
        prediction_loss_only=keep_pred_loss_only
    )


def validate_model(model, target_labels):
    num_labels = model.config.num_labels
    assert num_labels == len(target_labels), (
        f"Model num_labels={num_labels} "
        f"but FEATURES has {len(target_labels)} entries"
    )

def print_params(train_params, header="\nTraining Parameters/Details:"):
    print(header)
    for k, v in train_params.items():
        print(f"  {k}: {v}")

def setup_loggers(output_path):
    eval_logger = EvalLoggerCallback(output_file=output_path / "eval_metrics.json")
    train_logger = TrainingLoggerCallback(output_file=output_path / "train_metrics.json")
    return eval_logger, train_logger

def setup_loraconfig(params):
    return LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=params["rank"],
        lora_alpha=params["alpha"],
        lora_dropout=params["dropout"],
        target_modules=params["target_modules"],  
        bias="none"
    )

# Parse args here to avoid modifying
args = parse_args()
FEATURES = get_features(args.features_path)

# ---------------- Setup Paths ----------------
OUTPUT_PATH = Path(args.output_dir)

IS_RESUME = OUTPUT_PATH.exists()   # Check whether the script starts or resumes

# Get Last Checkpoint
LAST_CHECKPOINT = get_last_checkpoint(OUTPUT_PATH) if IS_RESUME else None

# Specify Paths for Training Args and LoRA Args
PARAMS_PATH = OUTPUT_PATH / "run_params.json" if IS_RESUME else args.train_params
LORA_PARAMS = OUTPUT_PATH / "lora_params.json" if IS_RESUME else args.lora_params

# Load Params from param file
print(f"\nLoading Training Parameters from {PARAMS_PATH}")
train_params = load_params(PARAMS_PATH)

# Add output_dir to train_params
train_params["output_dir"] = str(OUTPUT_PATH)

# Load LoRA params if LoRA
if args.lora_params:
    lora_params = load_params(LORA_PARAMS)


# ---------------- Load Model and Tokenizer ----------------
model, tokenizer = load_model(train_params["model"], args.use_automodel)
validate_model(model, target_labels=FEATURES)  # do some checks

# Initialize the Datasets
train_ds = load_from_disk(train_params["train_path"])
val_ds = load_from_disk(train_params["val_path"])

# Remove seq for faster processing
train_ds = train_ds.remove_columns(["seq"])
val_ds = val_ds.remove_columns(["seq"])

# Get basic param counts for the model
base_cnts = count_model_params(model)
print_model_params(base_cnts, "\nBase Model Parameter Counts")


# ---------------- Setup LoRA ------------------------------
if args.lora_params:
    lora_config = setup_loraconfig(lora_params)
    model = get_peft_model(model, lora_config)

    lora_cnts = count_model_params(model)
    print_model_params(lora_cnts, "\nLora-Applied Model Parameter Counts")
    
    # Get trainable_params for additional reference
    trainable_cnt = count_trainable_params(model)
    
    print_params(lora_params, "\nLoRA Hyperparameters")

# Print the Parameters
print_params(train_params)

if IS_RESUME:
    print(f"\nResuming Training from {LAST_CHECKPOINT}")
else:
    print(f"\nResults will be saved at {OUTPUT_PATH}")
    

# ---------------- Final Check to Proceed ----------------
# Check if user would like to PROCEED
do_proceed = input("Proceed Training (y/n)? ")

# Exit if not proceed
if not do_proceed.lower() in ["yes", "y"]:
    print("Exiting...")
    exit()

   
# Save Parameters for future reference
if not IS_RESUME:
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    save_params(OUTPUT_PATH / "run_params.json", train_params)
    save_params(OUTPUT_PATH / "lora_params.json", lora_params)
    save_params(OUTPUT_PATH / "trainable_params.json", trainable_cnt)
        

# ---------------- Setup Training Arguments ----------------
training_args = setup_training_args(train_params, LAST_CHECKPOINT, args.prediction_loss_only)

# ---------------- Setup Loggers and Trainer ----------------
eval_logger, train_logger = setup_loggers(OUTPUT_PATH)

trainer = MemmapEvalTrainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    data_collator=FloatLabelsCollator(tokenizer),
    compute_metrics=compute_metrics,
    callbacks=[
        EarlyStoppingCallback(
            early_stopping_patience=train_params["early_stopping_patience"],
            early_stopping_threshold=train_params["early_stopping_threshold"],
        ),
        eval_logger,
        train_logger,
    ],
)

eval_logger.trainer_ref = trainer

# ---------------- Train ----------------
trainer.train(resume_from_checkpoint=LAST_CHECKPOINT)

# ---------------- Final evaluation ----------------
metrics = trainer.evaluate()
trainer.save_metrics("eval", metrics)

# ---------------- Save minimal summary ----------------
summary = {
    "eval_loss": metrics["eval_loss"],
    "eval_auprc_macro": metrics.get("eval_auprc_macro"),
    "eval_auroc_macro": metrics.get("eval_auroc_macro"),
    "best_checkpoint": trainer.state.best_model_checkpoint,
}

with open(os.path.join(args.output_dir, "training_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

model = train_params["model"]
print(f"Finished training for model: {model}")
print(f"Best checkpoint: {trainer.state.best_model_checkpoint}")
