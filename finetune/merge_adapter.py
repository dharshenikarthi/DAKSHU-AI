"""
DAKSHU AI - Merge LoRA Adapter into Standalone Gemma Model
Merges fine-tuned LoRA weights back into the base model for deployment.
"""

import os
import sys
import argparse
from pathlib import Path

def merge_adapter(
    base_model_id: str = "google/gemma-2-2b-it",
    adapter_dir: str = "./model/dakshu-lora-adapter",
    output_dir: str = "./model/dakshu-merged"
):
    print("=" * 60)
    print("🔄 DAKSHU AI: Model & LoRA Adapter Merger")
    print(f"Base Model:    {base_model_id}")
    print(f"LoRA Adapter:  {adapter_dir}")
    print(f"Merged Output: {output_dir}")
    print("=" * 60)

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install via: pip install torch transformers peft")
        return

    if not os.path.exists(adapter_dir):
        print(f"❌ LoRA adapter not found at '{adapter_dir}'. Run 'python finetune/train_lora.py' first.")
        return

    print("📥 Loading base model into CPU/GPU memory...")
    tokenizer = AutoTokenizer.from_pretrained(adapter_dir)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16,
        device_map="auto" if torch.cuda.is_available() else "cpu"
    )

    print("🔗 Loading LoRA weights...")
    model = PeftModel.from_pretrained(base_model, adapter_dir)

    print("⚡ Merging LoRA layers into base model parameters...")
    merged_model = model.merge_and_unload()

    print(f"💾 Saving merged standalone model to {output_dir}...")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("\n✅ Merge successful!")
    print(f"Merged model is ready at: {output_dir}")
    print("\nYou can now:")
    print("1. Run directly with DAKSHU AI: set AI_BACKEND=transformers in .env")
    print("2. Convert to GGUF format for Ollama: python finetune/export_to_gguf.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA weights with Gemma base model")
    parser.add_argument("--base_model", type=str, default="google/gemma-2-2b-it", help="Base model ID")
    parser.add_argument("--adapter_dir", type=str, default="./model/dakshu-lora-adapter", help="Adapter path")
    parser.add_argument("--output_dir", type=str, default="./model/dakshu-merged", help="Output merged path")
    args = parser.parse_args()

    merge_adapter(
        base_model_id=args.base_model,
        adapter_dir=args.adapter_dir,
        output_dir=args.output_dir
    )

