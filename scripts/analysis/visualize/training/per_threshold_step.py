import argparse, json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import StrMethodFormatter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize a Line Graph given a metric from `eval_metrics.json` specifically per threshold."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to eval_metrics.json generated during training",
    )
    parser.add_argument(
        "--key",
        required=True,
        help="Key of the metric to visualize.",
    )
    parser.add_argument(
        "--key_label",
        help="Label to be specified in the graph",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Title of the plot to be generated."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="The location where the output files would be saved.",
    )
    parser.add_argument(
        "--output_fn",
        required=True,
        help="Filename of the output file.",
    )
    return parser.parse_args()

def read_json(path_to_file):
    try:
        with open(path_to_file, "r") as f:
            data = json.load(f)
            return data

    except FileNotFoundError:
        print("Error: The file 'data.json' was not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from the file. {e}")

def get_result_per_step(data, key):
    results = []
    for entry in data:
        stats = {
            "step": entry["step"],
            "epoch": entry["epoch"],
        }
        per_threshold = {
            th: vals[key]
            for th, vals in entry["eval_metrics_per_threshold"].items()
        }
        
        results.append(stats | per_threshold)
    return results

def to_df(data):
    df = pd.DataFrame(data)
    
    # Remove duplicate rows (i.e. final evaluation case)
    df.drop_duplicates(subset="step", inplace=True)
    
    return df

args = parse_args()
print(args)

print(f"Reading File: {args.input}")
data = read_json(args.input)

print(f"Forming the dataset...")
df = to_df(get_result_per_step(data, args.key))

# Melt the data for seaborn
threshold_cols = [c for c in df.columns if c not in ("step", "epoch")]
df_long = df.melt(
    id_vars=["step", "epoch"],
    value_vars=threshold_cols,
    var_name="threshold",
    value_name=args.key
)
df_long["threshold"] = df_long["threshold"].astype(str)

print(f"Plotting the data...")
sns.set_theme(style="ticks", font="Open Sans")
sns.set_context("paper")
fig, ax = plt.subplots(figsize=(9, 4))

sns.lineplot(
    data=df_long,
    x="step",
    y=args.key,
    hue="threshold",
    palette="Dark2",
    ax=ax
)
ax.set_xlabel("Training Step", fontweight="semibold", fontsize=10)
ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

if args.key_label is not None:
    y_label = args.key_label
else:
    y_label = args.key
ax.set_ylabel(y_label, fontweight="semibold", fontsize=10)

# ---- secondary x-axis (epoch) ----
ax_top = ax.twiny()
ax_top.set_xlim(ax.get_xlim())
epoch_ticks = df[df["epoch"] % 0.5 == 0]

ax_top.set_xticks(epoch_ticks["step"])
ax_top.set_xticklabels(epoch_ticks["epoch"])

ax_top.set_xlabel("Epoch", fontweight="semibold", fontsize=10)

ax.legend(
    title="Threshold",
    bbox_to_anchor=(1.02, 0.5),
    loc="center left",
    frameon=False,
)

plt.title(args.title, fontweight="semibold")
plt.tight_layout()

# Save to output file
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / f"{args.output_fn}.png"
print(f"Saving results to {output_file}")
plt.savefig(output_file, dpi=300)
plt.close()
