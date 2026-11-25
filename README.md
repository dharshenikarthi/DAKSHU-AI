# DAKSHU AI – Friendly Personal AI Companion

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg?logo=python)](https://python.org)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black.svg?logo=three.js)](https://threejs.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-d71f00.svg)](https://www.sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**DAKSHU AI** is a production-oriented, full-stack personal AI companion application. Designed to feel like a warm, supportive, and intelligent friend rather than a robotic assistant, Dakshu helps users learn difficult concepts, practice English fluency, explore startup and tech ideas, stay motivated, and converse naturally across **English, Tamil, and Tanglish**.

---

## 1. Key Capabilities & Modules

```
                             ┌───────────────────────┐
                             │       DAKSHU AI       │
                             │  Personal Companion   │
                             └───────────┬───────────┘
                                         │
        ┌───────────────┬────────────────┼───────────────┬───────────────┐
        ▼               ▼                ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ AI Companion │ │ Study Buddy  │ │English Fluency│ │ Idea Explorer│ │Voice Companion│
│ Casual chats,│ │Notes, quizzes│ │Grammar tips, │ │MVP roadmap,  │ │STT, TTS, 3D  │
│Tamil/Tanglish│ │code debugging│ │mock interview│ │architecture  │ │orb reaction  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### A. AI Companion
- Warm, empathetic conversational flow.
- Seamless code-switching across **English, Tamil, and Tanglish** ("Vanakkam!", "Epdi irukeenga?", "Kavalai padadheenga, let's solve this!").
- Proactive follow-up questions to understand what you need without being overly formal.

### B. Study Buddy
- Explains difficult computer science, math, and engineering topics using simple real-world analogies.
- Formats structured revision notes and generates interactive quizzes.
- Step-by-step programming error explanation and code generation.

### C. English Speaking Partner
- Safe, non-judgmental conversational English practice.
- Gentle, polite grammar feedback that highlights mistake reasons and offers natural phrasing alternatives.
- Tailored job interview drills and fluency confidence-building.

### D. Idea Explorer
- High-potential startup brainstorming and product discovery.
- Actionable 48-hour MVP execution blueprints and technology stack recommendations.

### E. Daily Motivation & Focus
- Realistic micro-goals, Pomodoro timing recommendations, and anti-burnout check-ins.

### F. Voice Companion
- Real-time browser speech recognition input.
- Text-to-speech voice synthesizer.
- Audio-reactive 3D orb pulsations during speech recognition and speech output.

---

## 2. Technology Stack

- **Frontend:** Semantic HTML5, CSS3 Custom Properties (Dark Navy `#060913`, Neon Violet/Cyan gradients, Glassmorphism), ES6 JavaScript modules, Three.js (r128) 3D Orb and Particle simulation, Lucide Icons, Marked.js (Markdown), Prism.js (Syntax Highlighting).
- **Backend:** Python 3.9+, FastAPI, Uvicorn, SQLAlchemy 2.0 ORM, Pydantic v2 schemas, Server-Sent Events (SSE) streaming engine.
- **Database:** SQLite (zero-config local development) and PostgreSQL (production).
- **AI Inference:** Modular `AIService` abstraction supporting **Google Gemma** (Gemma 4 E4B, Gemma 2 2B/9B) via Ollama, Hugging Face, OpenAI-compatible endpoints (Groq, vLLM, OpenRouter), and a Built-in Multilingual Gemma Neural-Heuristic Engine.
- **Security:** BCrypt password hashing, JWT HMAC-SHA256 bearer tokens, HTTPOnly cookies, CORS headers, isolated memory vaults.

---

## 3. Project Structure

```
DAKSHU_AI/
├── backend/
│   ├── main.py                # FastAPI entry point & static file routing
│   ├── config.py              # Application settings & environment loader
│   ├── database.py            # SQLAlchemy database engine & session dependency
│   ├── models.py              # Relational models (User, Conversation, Message, Memory, UserPreference)
│   ├── schemas.py             # Pydantic v2 validation models
│   ├── auth.py                # BCrypt hashing, JWT generation, & auth dependencies
│   ├── ai_service.py          # Modular Gemma inference orchestrator & system prompts
│   ├── memory_service.py      # Context assembly & user memory vault service
│   ├── requirements.txt       # Python dependencies
│   ├── routers/
│   │   ├── auth.py            # POST /api/auth/register, login, logout
│   │   ├── chat.py            # GET/POST/DELETE /api/conversations, /api/chat, /api/chat/stream
│   │   ├── memories.py        # GET/POST/DELETE /api/memories, /api/memories/preferences
│   │   └── profile.py         # GET/PUT /api/profile
│   └── migrations/            # Database migration documentation
├── frontend/
│   ├── index.html             # Landing page with interactive 3D hero orb
│   ├── chat.html              # Main AI chat application with real-time SSE stream
│   ├── login.html             # Secure glassmorphism login interface
│   ├── register.html          # Account registration
│   ├── profile.html           # Personal memory vault & preference manager
│   ├── css/
│   │   └── style.css          # Futuristic neon & glassmorphism theme
│   └── js/
│       ├── app.js             # Auth token storage, navbar sync, & toast notifications
│       ├── chat.js            # Streaming chat controller, markdown, & thread manager
│       ├── voice.js           # Web Speech API (STT & TTS) audio engine
│       └── three-scene.js     # Three.js 3D orb state machine & particle field
├── finetune/                  # Local Model Customization & Fine-Tuning Suite
│   ├── Modelfile              # Native Ollama Modelfile compiler for Dakshu
│   ├── dataset/
│   │   ├── train.jsonl        # Chat-formatted training pairs (English, Tamil, Tanglish)
│   │   └── validation.jsonl   # Validation pairs
│   ├── prepare_dataset.py     # Augmentation and Gemma chat-template formatter
│   ├── train_lora.py          # PyTorch + Hugging Face QLoRA fine-tuning script
│   ├── merge_adapter.py       # LoRA merger into standalone weights
│   ├── export_to_gguf.py      # GGUF converter for Ollama / llama.cpp
│   ├── dakshu_finetuning_colab.ipynb # 1-Click free Google Colab training notebook
│   ├── create_dakshu_ollama.ps1 # 1-Click PowerShell compiler
│   ├── create_dakshu_ollama.bat # 1-Click Windows batch compiler
│   └── README.md              # Detailed step-by-step fine-tuning guide
├── model/
│   ├── Modelfile              # Standalone Ollama Modelfile
│   └── README.md              # Gemma model setup, Ollama commands, & VRAM requirements
├── nginx/
│   └── dakshu.conf            # Production Nginx reverse proxy configuration with SSE support
├── tests/
│   └── test_backend.py        # Automated pytest test suite
├── .env                       # Active environment configuration
├── .env.example               # Template environment configuration
├── .gitignore                 # Version control exclusions
├── Dockerfile                 # Multi-stage container definition
├── docker-compose.yml         # Container orchestration with PostgreSQL
└── README.md                  # Comprehensive documentation
```

---

## 4. Local Installation & Setup

### Prerequisites
- Python 3.9, 3.10, or 3.11 installed.
- (Optional) [Ollama](https://ollama.com) installed if running Gemma models locally.

### Step 1: Clone Repository & Create Virtual Environment

**Windows PowerShell:**
```powershell
git clone <repository_url> DAKSHU_AI
cd DAKSHU_AI

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

**macOS / Linux:**
```bash
git clone <repository_url> DAKSHU_AI
cd DAKSHU_AI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### Step 2: Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Verify your `.env` settings:
```env
PROJECT_NAME="DAKSHU AI"
DEBUG=True
DATABASE_URL="sqlite:///./dakshu.db"

# AI Inference Backend: "builtin", "ollama", "huggingface", or "openai_compatible"
AI_BACKEND="builtin"

# If using Ollama:
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="gemma2:2b"
```

---

### Step 3: Run the Application

Start the FastAPI application with Uvicorn:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser to:
- **Landing Page:** [http://localhost:8000](http://localhost:8000)
- **AI Chat App:** [http://localhost:8000/chat.html](http://localhost:8000/chat.html)
- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 5. Local Model Setup & Custom Fine-Tuning

DAKSHU AI runs 100% locally with **zero external cloud APIs and zero subscription costs**.

### Option A: 1-Click Local Model Setup (Instant via Ollama Modelfile)
1. Install [Ollama](https://ollama.com).
2. Run the 1-click compiler:
   ```powershell
   # Windows PowerShell
   .\finetune\create_dakshu_ollama.ps1
   ```
   Or manually:
   ```bash
   ollama pull gemma2:2b
   ollama create dakshu -f finetune/Modelfile
   ollama run dakshu
   ```
3. Your `.env` is already configured:
   ```env
   AI_BACKEND=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=dakshu
   OLLAMA_FALLBACK_MODEL=gemma2:2b
   ```

### Option B: Free Google Colab 1-Click QLoRA Fine-Tuning
Train the model on a free GPU with custom multi-turn Tanglish/Tamil/English pairs:
1. Open `finetune/dakshu_finetuning_colab.ipynb` in [Google Colab](https://colab.research.google.com).
2. Run all cells on a free T4 GPU.
3. Download the resulting `dakshu-q4_k_m.gguf` into `./model/`.

### Option C: Local PyTorch QLoRA Fine-Tuning
```bash
pip install -r finetune/requirements.txt
python finetune/train_lora.py --base_model google/gemma-2-2b-it --epochs 3
python finetune/merge_adapter.py
python finetune/export_to_gguf.py
```
See the complete guide in [finetune/README.md](file:///c:/Dharsheni/DAKSHU%20AI/finetune/README.md).

---

## 6. Running Automated Tests

Run the complete automated pytest suite:

```bash
pytest tests/ -v
```

The test suite validates:
- `test_health_check`: API, database, and model provider health.
- `test_user_registration`: Account creation and email uniqueness.
- `test_user_login_success` & `test_user_login_invalid_password`: BCrypt verification.
- `test_user_logout`: Session cookie invalidation.
- `test_user_profile_and_preferences`: Retrieval and live preference updates.
- `test_personal_memory_crud`: Storing, querying, and deleting explicit facts.
- `test_conversations_crud`: Conversation lifecycle and message persistence.
- `test_chat_endpoint_companion`: AI response generation.
- `test_chat_multilingual_tamil_tanglish`: Code-switching and Tanglish understanding.
- `test_chat_study_buddy_module`: Concept breakdowns and quizzes.
- `test_chat_english_partner_module`: Grammar feedback.
- `test_chat_stream_endpoint`: Server-Sent Events (SSE) data chunk delivery.
- `test_unauthorized_access_denied`: Route protection and token authorization.

---

## 7. Cloud Deployment (Vercel, Render, Railway, Netlify, AWS EC2)

DAKSHU AI includes turnkey configurations for modern cloud platforms:

- **Vercel (All-in-One Full-Stack):** Configured via [`vercel.json`](file:///c:/Dharsheni/DAKSHU%20AI/vercel.json) and [`api/index.py`](file:///c:/Dharsheni/DAKSHU%20AI/api/index.py).
- **Render.com (Recommended for FastAPI & SSE):** 1-click blueprint via [`render.yaml`](file:///c:/Dharsheni/DAKSHU%20AI/render.yaml).
- **Railway.app:** Auto-detected via [`Procfile`](file:///c:/Dharsheni/DAKSHU%20AI/Procfile).
- **Netlify:** Static frontend hosting via [`netlify.toml`](file:///c:/Dharsheni/DAKSHU%20AI/netlify.toml).
- **AWS EC2 & Docker:** Containerized deploy via [`Dockerfile`](file:///c:/Dharsheni/DAKSHU%20AI/Dockerfile) and [`docker-compose.yml`](file:///c:/Dharsheni/DAKSHU%20AI/docker-compose.yml).

👉 **For complete step-by-step cloud instructions, read [DEPLOYMENT.md](file:///c:/Dharsheni/DAKSHU%20AI/DEPLOYMENT.md).**

---

### Architecture on AWS EC2
```
  [User Browser]
         │ (HTTPS 443)
         ▼
  [Nginx Reverse Proxy]  <── Let's Encrypt SSL
         │ (Internal HTTP 8000 / SSE buffer off)
         ▼
  [FastAPI (Uvicorn / Systemd)]
    ├── [PostgreSQL Database]
    └── [Gemma Inference / Ollama / API Gateway]
```

### Step 1: Provision EC2 Instance
- **AMI:** Ubuntu 22.04 LTS or 24.04 LTS (x86_64).
- **Instance Type:** `t3.large` (for cloud API / Builtin model) or `g4dn.xlarge` (with NVIDIA T4 GPU for local Ollama Gemma inference).
- **Security Group:** Open ports `22` (SSH), `80` (HTTP), and `443` (HTTPS).

### Step 2: System Packages & PostgreSQL Setup
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx postgresql postgresql-contrib

# Setup PostgreSQL Database
sudo -u postgres psql -c "CREATE DATABASE dakshu_db;"
sudo -u postgres psql -c "CREATE USER dakshu_user WITH ENCRYPTED PASSWORD 'YourStrongPassword123!';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dakshu_db TO dakshu_user;"
```

### Step 3: Clone Code & Configure Environment
```bash
sudo mkdir -p /var/www/dakshu
sudo chown -R ubuntu:ubuntu /var/www/dakshu
git clone <repository_url> /var/www/dakshu
cd /var/www/dakshu

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Configure Production .env
cat <<EOF > .env
PROJECT_NAME="DAKSHU AI"
DEBUG=False
SECRET_KEY="$(openssl rand -hex 32)"
DATABASE_URL="postgresql://dakshu_user:YourStrongPassword123!@localhost:5432/dakshu_db"
AI_BACKEND="builtin"
EOF
```

### Step 4: Configure Systemd Daemon Service
Create `/etc/systemd/system/dakshu.service`:
```ini
[Unit]
Description=DAKSHU AI FastAPI Application Service
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/dakshu
Environment="PATH=/var/www/dakshu/venv/bin"
ExecStart=/var/www/dakshu/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 3
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dakshu
sudo systemctl start dakshu
sudo systemctl status dakshu
```

### Step 5: Configure Nginx & SSL
Copy `nginx/dakshu.conf` to `/etc/nginx/sites-available/dakshu.conf`, update your domain name, and link it:

```bash
sudo ln -s /etc/nginx/sites-available/dakshu.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Install free Let's Encrypt SSL with Certbot
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d dakshu.yourdomain.com
```

---

## 8. Docker Deployment

To spin up Dakshu AI with PostgreSQL via Docker Compose:

```bash
docker compose up -d --build
```

To view logs:
```bash
docker compose logs -f
```

---

## 9. Security & Privacy Guarantees

1. **Password Security:** All user credentials are protected using salted BCrypt encryption. Raw passwords are never logged or stored.
2. **Token Security:** Authentication uses cryptographically signed JWT tokens with configurable TTL and optional HTTPOnly, SameSite cookies.
3. **Data Isolation:** User chats and memories are strictly isolated with relational foreign keys (`ON DELETE CASCADE`).
4. **Memory Transparency:** Dakshu only remembers explicit facts saved in your Memory Vault. Users can inspect, search, or purge any memory with immediate database deletion.
5. **No Client-Side Secrets:** API keys and model configurations remain server-side in `.env` and are never exposed in frontend JavaScript bundles.

---

## 10. Limitations & Boundaries

- **Voice Synthesis:** Relies on browser-native SpeechRecognition and SpeechSynthesis APIs. Speech recognition requires HTTPS in production and microphone permissions granted in the browser.
- **Hardware Limitations:** Running large open-weight models (e.g. Gemma 2 9B or Gemma 4) locally requires a modern GPU with 8GB to 16GB of VRAM. For systems without dedicated GPUs, the built-in companion engine or hosted OpenAI-compatible endpoint should be configured.
- **Companion Nature:** Dakshu is an empathetic companion and tutor. It does not replace professional medical, legal, or licensed mental health counseling.

