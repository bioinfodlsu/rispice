from transformers import BertConfig, BertForSequenceClassification, AutoTokenizer, AutoModelForSequenceClassification
import argparse, os

parser = argparse.ArgumentParser(description="Download a model via HuggingFace")
parser.add_argument(
    "--model", 
    required=True, 
    help="model_name to download from huggingface"
)
parser.add_argument(
    "--num_of_labels", 
    required=True, 
    help="number of labels of the modified model"
)
parser.add_argument(
    "--use_automodel", 
    action="store_true", 
    help="number of labels of the modified model"
)
parser.add_argument("--output_path", help="location where the model will be saved")

args = parser.parse_args()

print(args)
print("Checking BERT Model")

MODEL_NAME = args.model
LABEL_CNT = int(args.num_of_labels)
OUTPUT_PATH = args.output_path

if args.use_automodel:
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=LABEL_CNT,
        problem_type="multi_label_classification",
        trust_remote_code=True
    )
else:
    config = BertConfig.from_pretrained(
        MODEL_NAME, 
        num_labels=LABEL_CNT, 
        problem_type="multi_label_classification"
    )
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME, config=config)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

print("Loaded the Model: ", model)
print(f"Param Count: {model.num_parameters():,}")

for name, param in model.named_parameters():
    if not param.requires_grad:
        print(name)

# Save the Model if output_path is provided
if OUTPUT_PATH is not None:
    # Create folders if does not exist
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH, exist_ok=True)

    # Save the model
    model.save_pretrained(OUTPUT_PATH)
    tokenizer.save_pretrained(OUTPUT_PATH)
    print(f"Model and Tokenizer has been saved to {OUTPUT_PATH}")
