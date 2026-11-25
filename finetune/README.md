# 🚀 DAKSHU AI: Local Model & Fine-Tuning Guide

This guide walks you through customizing and fine-tuning **Google Gemma 2** locally to embody Dakshu's warm, multilingual personality (English, Tamil, Tanglish) and specialized modules.

---

## ⚡ Method 1: Instant 10-Second Fine-Tuning (Recommended)

The fastest and most reliable way to run Dakshu locally is using the **Native Ollama Modelfile**. This compiles Dakshu's exact system persona, multilingual prompts, sampling hyperparameters, and turn delimiters directly into a custom local model called `dakshu`.

### Prerequisites:
1. Download & install Ollama from [https://ollama.com](https://ollama.com).
2. Start the Ollama app (or run `ollama serve`).

### 1-Command Build:
```bash
# 1. Pull the base Gemma 2 2B model
ollama pull gemma2:2b

# 2. Compile Dakshu using the custom Modelfile
ollama create dakshu -f finetune/Modelfile

# 3. Test Dakshu directly in terminal
ollama run dakshu
```

When you type:
> *"Vanakkam Dakshu! How are you?"*

Dakshu will reply in warm Tanglish with its custom persona!

---

## ☁️ Method 2: One-Click Google Colab Fine-Tuning (Free GPU)

If your laptop doesn't have an NVIDIA GPU with 8GB+ VRAM, you can train Dakshu on a free Google Colab GPU (T4 / L4) in under 10 minutes:

1. Open [Google Colab](https://colab.research.google.com).
2. Upload `finetune/dakshu_finetuning_colab.ipynb` and `finetune/dataset/train.jsonl`.
3. In Colab menu: **Runtime → Change runtime type → T4 GPU**.
4. Click **Runtime → Run all**.
5. The notebook will:
   - Load `unsloth/gemma-2-2b-it` in 4-bit.
   - Attach LoRA adapters to all attention and MLP projection layers.
   - Fine-tune on `train.jsonl` with SFTTrainer.
   - Export `dakshu-q4_k_m.gguf`.
6. Download `dakshu-q4_k_m.gguf` to `c:\Dharsheni\DAKSHU AI\model\`.
7. Import into Ollama:
   ```bash
   ollama create dakshu -f model/Modelfile
   ```

---

## 💻 Method 3: Full Local QLoRA Fine-Tuning (PyTorch & Hugging Face)

For advanced machine learning engineers training on a local workstation:

### 1. Install Dependencies:
```bash
pip install -r finetune/requirements.txt
```

### 2. Prepare & Augment Dataset:
```bash
python finetune/prepare_dataset.py
```
This generates `train.jsonl` and `validation.jsonl` formatted with Gemma chat turns.

### 3. Run QLoRA Training:
```bash
python finetune/train_lora.py --base_model google/gemma-2-2b-it --epochs 3 --batch_size 2
```
This saves LoRA adapter weights in `./model/dakshu-lora-adapter`.

### 4. Merge Adapter with Base Model:
```bash
python finetune/merge_adapter.py
```
This produces `./model/dakshu-merged`.

### 5. Export to GGUF for Ollama:
```bash
python finetune/export_to_gguf.py
```

---

## 🔌 Connecting to DAKSHU AI Application

In your project root `.env` file:
```env
# Switch from Groq to Local Ollama
AI_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=dakshu
OLLAMA_FALLBACK_MODEL=gemma2:2b
```

### Zero-Downtime Fallback:
If Ollama is stopped or booting up, DAKSHU AI's backend automatically engages the **Built-in Multilingual Companion Engine**, ensuring that the chat UI never hangs or throws 500 errors!

