import itertools, subprocess, json
from tqdm import tqdm
from pathlib import Path

# --- Directories ---
BASE_OUT_DIR = Path("outputs/tune")
BASE_OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DIR = Path("models/base/3mer")
TRAIN_DIR = Path("data/finetune/histone/merged/sim1k_train")
VAL_DIR = Path("data/finetune/histone/merged/sim1k_val")


# --- Hyperparameters ---
lrs = [1e-4, 5e-5]
batch_sizes = [16, 32]
weight_decays = [0.0, 0.01]

results = []


# --- Grid search ---
for lr, bs, wd in tqdm(
    itertools.product(lrs, batch_sizes, weight_decays),
    total=len(lrs) * len(batch_sizes) * len(weight_decays),
    desc="Hyperparam GridSearch",
):
    run_name = f"lr{lr}_bs{bs}_wd{wd}"
    out_dir = BASE_OUT_DIR / run_name
    out_dir.mkdir(exist_ok=True)  # ensure folder exists
    
    print(f"Executing {run_name}")

    final_metrics_file = out_dir / "final_metrics.json"
    if final_metrics_file.exists():
        print(f"Skipping {run_name} (already done)")
        continue

    cmd = [
        "python", "-m", "scripts.finetuning.train",
        "--model", MODEL_DIR,
        "--train", TRAIN_DIR,
        "--val", VAL_DIR,
        "--learning_rate", str(lr),
        "--batch_size", str(bs),
        "--weight_decay", str(wd),
        "--output_dir", str(out_dir),
    ]

    subprocess.run(cmd, check=True)

    # --- Read metrics ---
    with open(final_metrics_file) as f:
        metrics = json.load(f)

    results.append((run_name, metrics["eval_f1_micro"]))


# --- Sort and save ---
results_sorted = sorted(results, key=lambda x: x[1], reverse=True)
print(results_sorted)

with open(BASE_OUT_DIR / "tuning_results.json", 'w') as json_file:
    json.dump(results_sorted, json_file, indent=4)
