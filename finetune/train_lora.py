"""
DAKSHU AI - QLoRA Fine-Tuning Pipeline for Google Gemma 2
Fine-tunes the base model on Dakshu's friendly multilingual companion dataset.
"""

import os
import sys
import argparse
from pathlib import Path

def train_dakshu(
    base_model_id: str = "google/gemma-2-2b-it",
    train_file: str = "finetune/dataset/train.jsonl",
    val_file: str = "finetune/dataset/validation.jsonl",
    output_dir: str = "./model/dakshu-lora-adapter",
    epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    lora_r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    max_seq_length: int = 1024,
):
    print("=" * 60)
    print("🚀 DAKSHU AI: QLoRA Fine-Tuning Pipeline")
    print(f"Base Model:       {base_model_id}")
    print(f"Training Data:    {train_file}")
    print(f"Validation Data:  {val_file}")
    print(f"Output Directory: {output_dir}")
    print(f"Epochs:           {epochs}")
    print(f"Learning Rate:    {learning_rate}")
    print("=" * 60)

    try:
        import torch
        from datasets import load_dataset
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments
        )
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from trl import SFTTrainer
    except ImportError as e:
        print(f"\n❌ Missing required fine-tuning dependencies: {e}")
        print("Install them by running:")
        print("  pip install -r finetune/requirements.txt")
        print("\nOr run the Google Colab Notebook at: finetune/dakshu_finetuning_colab.ipynb")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🖥️ Target Compute Device: {device.upper()}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    # 1. Quantization Configuration (QLoRA 4-bit)
    bnb_config = None
    if device == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

    # 2. Load Tokenizer & Model
    print(f"📥 Loading base model: {base_model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        quantization_config=bnb_config,
        device_map="auto" if device == "cuda" else None,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        trust_remote_code=True
    )

    if device == "cuda":
        model = prepare_model_for_kbit_training(model)

    # 3. LoRA Configuration targeting all linear projection layers
    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj"
        ]
    )

    model = get_peft_model(model, lora_config)
    print("\n📊 Trainable Parameter Distribution:")
    model.print_trainable_parameters()

    # 4. Load Dataset
    print(f"\n📂 Loading datasets...")
    data_files = {"train": train_file}
    if os.path.exists(val_file):
        data_files["validation"] = val_file
    dataset = load_dataset("json", data_files=data_files)

    # 5. Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="epoch",
        evaluation_strategy="epoch" if "validation" in dataset else "no",
        fp16=(device == "cuda"),
        bf16=False,
        max_grad_norm=0.3,
        report_to="none"
    )

    # 6. SFTTrainer Execution
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("validation", None),
        peft_config=lora_config,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        tokenizer=tokenizer,
        args=training_args,
    )

    print("\n🔥 Starting Fine-Tuning on Dakshu's Persona Dataset...")
    trainer.train()

    # 7. Save Adapter & Tokenizer
    print(f"\n💾 Saving fine-tuned LoRA adapter to {output_dir}...")
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("\n✅ Fine-tuning completed successfully!")
    print(f"Adapter saved at: {output_dir}")
    print("Next step: Merge with base model using 'python finetune/merge_adapter.py'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Gemma 2 for Dakshu AI")
    parser.add_argument("--base_model", type=str, default="google/gemma-2-2b-it", help="Base Gemma model ID")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--output_dir", type=str, default="./model/dakshu-lora-adapter", help="Output path")
    args = parser.parse_args()

    train_dakshu(
        base_model_id=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        output_dir=args.output_dir
    )

