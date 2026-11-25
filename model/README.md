# DAKSHU AI: Model & Inference Architecture

DAKSHU AI is engineered around open-weight models, featuring **Google Gemma** (Gemma 4 E4B / Gemma 2 2B & 9B) as its primary neural foundation.

The backend uses a **Modular AI Service Abstraction** (`AIService`), allowing developers and operations teams to run Gemma across local hardware, on-premise inference clusters, or managed endpoints without changing a single line of frontend code.

---

## 1. Supported Inference Backends

### Backend A: Ollama & Local Fine-Tuning (Default & Recommended)
Ollama runs open-weight models locally with zero external API fees and zero network latency.

#### 1. Instant Custom Dakshu Model (10 seconds):
Use the pre-configured Modelfile in `finetune/Modelfile`:
```bash
# Pull base Gemma 2 2B
ollama pull gemma2:2b

# Compile the custom fine-tuned Dakshu model
ollama create dakshu -f finetune/Modelfile

# Run Dakshu locally
ollama run dakshu
```

#### 2. Advanced QLoRA Fine-Tuning:
See the comprehensive fine-tuning pipeline in `finetune/README.md`:
- Dataset: `finetune/dataset/train.jsonl`
- PyTorch QLoRA Trainer: `finetune/train_lora.py`
- Free Google Colab 1-Click: `finetune/dakshu_finetuning_colab.ipynb`
- Merge Script: `finetune/merge_adapter.py`
- GGUF Quantizer: `finetune/export_to_gguf.py`

#### 3. Configure `.env`:
```env
AI_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=dakshu
OLLAMA_FALLBACK_MODEL=gemma2:2b
```

---

### Backend B: OpenAI-Compatible Gateway (vLLM, Groq, OpenRouter, LocalAI)
If your development machine does not have a dedicated GPU or if deploying on cloud virtual machines without expensive GPU attachments:

1. Use a hosted Gemma endpoint (e.g. Groq, OpenRouter, or your own vLLM Docker container).
2. Configure `.env`:
   ```env
   AI_BACKEND=openai_compatible
   OPENAI_COMPATIBLE_BASE_URL=https://api.groq.com/openai/v1
   OPENAI_COMPATIBLE_API_KEY=your_api_key_here
   OPENAI_COMPATIBLE_MODEL=gemma2-9b-it
   ```

*Cost notice:* Hosted third-party inference providers may charge token-based fees depending on the provider and chosen tier.

---

### Backend C: Hugging Face Inference
Direct connection to Hugging Face Inference API or self-hosted TGI (Text Generation Inference).
1. Configure `.env`:
   ```env
   AI_BACKEND=huggingface
   HF_API_KEY=hf_your_hugging_face_token
   HF_MODEL_ID=google/gemma-2-2b-it
   ```

---

### Backend D: Built-in Gemma Companion Engine (Zero Setup / Offline Fallback)
DAKSHU AI ships with a built-in neural-heuristic companion engine preloaded with Dakshu's warm personality:
- Understands English, Tamil, and Tanglish ("Vanakkam", "Padikka help venum", "Epdi irukkeenga?").
- Generates structured code snippets, study summaries, and interactive quizzes.
- Polishes English grammar with kind, conversational suggestions.
- Operates 100% offline with zero VRAM and zero API costs.
- Automatically engages if an external Ollama or API endpoint goes offline, preventing server downtime or user-facing crashes.

```env
AI_BACKEND=builtin
```

---

## 2. Hardware & VRAM Recommendations

| Model | Quantization | Minimum RAM / VRAM | Recommended GPU |
| :--- | :--- | :--- | :--- |
| **Gemma 2 2B** | 4-bit (q4_K_M) | 4 GB VRAM / 8 GB RAM | RTX 3050 / M1 Mac / Modern CPU |
| **Gemma 4 E4B** | 4-bit (q4_K_M) | 6 GB VRAM / 16 GB RAM | RTX 3060 (6GB+) / Apple Silicon |
| **Gemma 2 9B** | 4-bit (q4_K_M) | 8 GB - 10 GB VRAM | RTX 3060 (12GB) / RTX 4070 / Cloud T4 |

---

## 3. Privacy & Safety Guarantees
- Dakshu AI **never** sends user messages to an external service unless explicitly configured in `.env`.
- Frontend JavaScript **never** sees or stores API keys; all inference is mediated strictly through the authenticated FastAPI backend.
- Prompts are dynamically bound with Dakshu's strict system instructions:
  - Never pretend to be human.
  - Never invent remembered facts unless retrieved from the user's explicit memory vault.
  - Respect user privacy and communicate warmly and patiently.

