import os
from datasets import load_dataset, Dataset
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import numpy as np
import torch
from sklearn.model_selection import train_test_split

# CONFIG
MODEL_NAME = "distilbert-base-uncased"   # small, fast
OUT_DIR = "models/prompt_injection_detector"
BATCH_SIZE = 16
EPOCHS = 2
MAX_LENGTH = 256
SEED = 42

# If your parquet is local
# df = pd.read_parquet("data/train-00000-of-00001-9564e8b05b4757ab.parquet")
# If you want to read HF dataset directly (alternative)
# ds = load_dataset("deepset/prompt-injections", split="train")  # if available

# Example: load parquet with pandas (replace path as needed)
df = pd.read_parquet("data/train-00000-of-00001-9564e8b05b4757ab.parquet")

# Inspect expected columns: you need a text column and a label column.
# Adjust these names to match your dataset (e.g., 'prompt', 'label' or 'score')
print(df.columns)
# Example: assume df has 'prompt' and 'label' where label is 0/1 or 0..100
text_col = "text"
label_col = "label"   # change if different

# If labels are continuous 0..100 and you want to train regression:
is_regression = df[label_col].dtype.kind in "fi" and df[label_col].max() > 1

# For binary classification convert label > threshold to 1/0 if needed:
if not is_regression:
    # Ensure labels are 0/1
    df[label_col] = df[label_col].astype(int)

# Split
train_df, val_df = train_test_split(df[[text_col, label_col]], test_size=0.1, random_state=SEED, shuffle=True, stratify=None)

# Convert to HF datasets
train_ds = Dataset.from_pandas(train_df.reset_index(drop=True))
val_ds = Dataset.from_pandas(val_df.reset_index(drop=True))

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

def preprocess(batch):
    tokens = tokenizer(batch[text_col], truncation=True, padding='max_length', max_length=MAX_LENGTH)
    if is_regression:
        tokens["labels"] = [float(x) for x in batch[label_col]]
    else:
        tokens["labels"] = [int(x) for x in batch[label_col]]
    return tokens

train_ds = train_ds.map(preprocess, batched=True, remove_columns=train_ds.column_names)
val_ds = val_ds.map(preprocess, batched=True, remove_columns=val_ds.column_names)

if is_regression:
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, problem_type="regression", num_labels=1)
else:
    num_labels = int(df[label_col].nunique())
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels)

training_args = TrainingArguments(
    output_dir=OUT_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=EPOCHS,
    logging_steps=100,
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    fp16=torch.cuda.is_available(),
)

# Simple metric function: MSE for regression, accuracy for classification
import evaluate
metrics = {}
if is_regression:
    metric = evaluate.load("mean_squared_error")
    def compute_metrics(eval_pred):
        preds, labels = eval_pred
        if isinstance(preds, tuple): preds = preds[0]
        preds = preds.squeeze()
        return {"mse": float(metric.compute(predictions=preds, references=labels)["mean_squared_error"])}
else:
    acc = evaluate.load("accuracy")
    def compute_metrics(eval_pred):
        preds, labels = eval_pred
        preds = np.argmax(preds, axis=1)
        return {"accuracy": float(acc.compute(predictions=preds, references=labels)["accuracy"])}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    compute_metrics=compute_metrics,
    tokenizer=tokenizer,
)

trainer.train()
trainer.save_model(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print("Saved model to", OUT_DIR)