"""
DAKSHU AI - Export Merged Model to GGUF format for Ollama / llama.cpp
"""

import os
import sys
import subprocess
from pathlib import Path

def export_gguf(
    model_dir: str = "./model/dakshu-merged",
    output_gguf: str = "./model/dakshu-q4_k_m.gguf",
    quantization: str = "q4_k_m"
):
    print("=" * 60)
    print("📦 DAKSHU AI: GGUF Exporter for Ollama")
    print(f"Input Model:      {model_dir}")
    print(f"Output GGUF:      {output_gguf}")
    print(f"Quantization:     {quantization}")
    print("=" * 60)

    if not os.path.exists(model_dir):
        print(f"❌ Input model directory '{model_dir}' not found.")
        print("Please run 'python finetune/merge_adapter.py' first.")
        return

    print("\n🛠️ GGUF Conversion Workflow:")
    print("1. Clone llama.cpp if not present:")
    print("   git clone https://github.com/ggerganov/llama.cpp")
    print("   pip install -r llama.cpp/requirements.txt")
    print("\n2. Convert HF weights to FP16 GGUF:")
    print(f"   python llama.cpp/convert_hf_to_gguf.py {model_dir} --outfile ./model/dakshu-f16.gguf")
    print("\n3. Quantize to 4-bit (compact, fast CPU/GPU inference):")
    print(f"   ./llama.cpp/llama-quantize ./model/dakshu-f16.gguf {output_gguf} {quantization}")
    print("\n4. Create custom Ollama model:")
    print("   echo 'FROM " + output_gguf + "' > ./model/Modelfile.gguf")
    print("   cat finetune/Modelfile >> ./model/Modelfile.gguf")
    print("   ollama create dakshu -f ./model/Modelfile.gguf")
    print("\n5. Run Dakshu locally:")
    print("   ollama run dakshu")
    print("=" * 60)

if __name__ == "__main__":
    export_gguf()

