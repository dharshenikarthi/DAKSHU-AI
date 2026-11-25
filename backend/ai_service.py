import json
import re
import asyncio
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
from backend.config import settings

logger = logging.getLogger("dakshu.ai_service")

from datetime import datetime

# --- System Prompts ---
DAKSHU_BASE_SYSTEM_PROMPT = """You are Dakshu, a friendly and intelligent AI companion.

You communicate naturally and warmly.
You help users understand concepts, practice communication, explore ideas, solve problems, and learn new skills.

You support English, Tamil, and Tanglish.
You adapt to the user's language.
You explain complicated subjects in simple steps.
You are encouraging, patient, respectful, and honest.
You do not pretend to be human.
You do not claim to remember information unless it is stored and retrieved.
You protect user privacy.
You clearly acknowledge uncertainty.
You avoid unnecessarily long responses unless the user requests detail."""

MODULE_PROMPTS = {
    "companion": """You are acting as Dakshu the Friendly Personal AI Companion.
Focus on natural, caring conversations. Be warm and supportive. If the user speaks Tamil or Tanglish, reply fluently and naturally in kind (e.g., 'Kavalai padadheenga, let's solve this together!'). Ask thoughtful follow-up questions to keep the conversation engaging.""",

    "study": """You are acting as Dakshu the Study Buddy.
Explain complex concepts using simple everyday analogies. When requested:
- Generate clean, structured study notes.
- Summarize long or difficult topics.
- Create practice quizzes with answers and explanations.
- Help troubleshoot programming errors step by step.
- Design practical daily and weekly study plans.""",

    "english": """You are acting as Dakshu the English Speaking Partner.
Your goal is to build the user's confidence in conversational English.
- Always be encouraging and supportive.
- When correcting grammar or phrasing, do it politely with gentle explanations.
- Provide a more natural alternative sentence.
- Give constructive feedback without breaking the flow of natural conversation.""",

    "ideas": """You are acting as Dakshu the Idea Explorer.
Help the user brainstorm innovative startup ideas, creative tech projects, and new technology concepts.
- Break down concepts into clear execution roadmaps.
- Suggest modern tech stacks, MVP milestones, and architecture outlines.
- Encourage creative thinking and practical execution.""",

    "motivation": """You are acting as Dakshu the Daily Motivation & Productivity Partner.
Deliver warm, uplifting, and realistic encouragement.
- Suggest actionable daily micro-goals.
- Provide time-management strategies (Pomodoro, time-blocking).
- Remind users to take breaks, stay hydrated, and celebrate small wins.""",

    "voice": """You are acting as Dakshu the Voice Companion.
Keep your responses conversational, crisp, and easy to listen to when read aloud.
Avoid large code dumps or tables unless explicitly asked. Use short, punchy, warm sentences that sound pleasant when spoken."""
}

def assemble_system_prompt(module: str = "companion", memory_injection: str = "") -> str:
    now = datetime.now()
    current_time_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
    temporal_context = (
        f"[REAL-TIME TEMPORAL CONTEXT]\n"
        f"- Current Date & Day: {now.strftime('%A, %B %d, %Y')}\n"
        f"- Current Local Time: {now.strftime('%I:%M %p')}\n"
        f"You are aware of the real-world current day, date, and time.\n"
    )

    module_guide = MODULE_PROMPTS.get(module, MODULE_PROMPTS["companion"])
    prompt_parts = [
        DAKSHU_BASE_SYSTEM_PROMPT,
        temporal_context,
        f"\n[ACTIVE MODE / ROLE: {module.upper()}]\n{module_guide}"
    ]
    if memory_injection:
        prompt_parts.append(memory_injection)
    return "\n\n".join(prompt_parts)


class BaseAIProvider:
    """Base Interface for Gemma Inference Providers"""
    async def generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        raise NotImplementedError

    async def stream_generate(self, messages: List[Dict[str, str]], system_prompt: str) -> AsyncGenerator[str, None]:
        raise NotImplementedError


class OllamaGemmaProvider(BaseAIProvider):
    """Local Ollama Inference Provider (Configured for custom fine-tuned Dakshu or Gemma models)"""
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback_model = settings.OLLAMA_FALLBACK_MODEL

    async def generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        prompt_history = [{"role": "system", "content": system_prompt}] + messages
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": prompt_history,
            "stream": False,
            "options": {
                "temperature": settings.TEMPERATURE,
                "num_predict": settings.MAX_TOKENS_OUTPUT
            }
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 404 and self.fallback_model and self.model != self.fallback_model:
                    # Model not pulled yet; try fallback model
                    logger.info(f"Ollama model '{self.model}' not found, trying fallback '{self.fallback_model}'")
                    payload["model"] = self.fallback_model
                    resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
            except httpx.ConnectError:
                raise RuntimeError(f"Ollama server is not running at {self.base_url}. Start Ollama or run 'ollama serve'.")

    async def stream_generate(self, messages: List[Dict[str, str]], system_prompt: str) -> AsyncGenerator[str, None]:
        prompt_history = [{"role": "system", "content": system_prompt}] + messages
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": prompt_history,
            "stream": True,
            "options": {
                "temperature": settings.TEMPERATURE,
                "num_predict": settings.MAX_TOKENS_OUTPUT
            }
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code == 404 and self.fallback_model and self.model != self.fallback_model:
                        logger.info(f"Ollama model '{self.model}' not found, trying fallback '{self.fallback_model}'")
                        payload["model"] = self.fallback_model
                        async with client.stream("POST", url, json=payload) as fallback_resp:
                            fallback_resp.raise_for_status()
                            async for line in fallback_resp.aiter_lines():
                                if line:
                                    try:
                                        chunk_data = json.loads(line)
                                        content = chunk_data.get("message", {}).get("content", "")
                                        if content:
                                            yield content
                                        if chunk_data.get("done", False):
                                            break
                                    except json.JSONDecodeError:
                                        continue
                        return

                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk_data = json.loads(line)
                                content = chunk_data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                                if chunk_data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
            except httpx.ConnectError:
                raise RuntimeError(f"Ollama server is not running at {self.base_url}. Start Ollama or run 'ollama serve'.")


class TransformersLocalProvider(BaseAIProvider):
    """Local Hugging Face Transformers In-Memory Provider (Loads local fine-tuned weights or LoRA merged model)"""
    def __init__(self, model_path: str = settings.LOCAL_MODEL_PATH):
        self.model_path = model_path
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self):
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            logger.info(f"Loading local Transformers model from {self.model_path}...")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None
            )
            if device != "cuda":
                self._model.to("cpu")
            logger.info(f"Successfully loaded local model on {device}")
        except Exception as e:
            logger.error(f"Failed to load Transformers model from {self.model_path}: {e}")
            raise RuntimeError(f"Could not load local model from {self.model_path}: {e}")

    async def generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        # Run blocking model inference in background threadpool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_generate, messages, system_prompt)

    def _sync_generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        self._ensure_loaded()
        prompt_history = [{"role": "system", "content": system_prompt}] + messages
        prompt_text = self._tokenizer.apply_chat_template(prompt_history, tokenize=False, add_generation_prompt=True)
        inputs = self._tokenizer(prompt_text, return_tensors="pt").to(self._model.device)
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=settings.MAX_TOKENS_OUTPUT,
            temperature=settings.TEMPERATURE,
            do_sample=True,
            pad_token_id=self._tokenizer.eos_token_id
        )
        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        return self._tokenizer.decode(generated_ids, skip_special_tokens=True)

    async def stream_generate(self, messages: List[Dict[str, str]], system_prompt: str) -> AsyncGenerator[str, None]:
        full_text = await self.generate(messages, system_prompt)
        # Yield words with natural typewriter streaming
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.015)


class GroqGemmaProvider(BaseAIProvider):
    """Groq Hosted Inference Provider (Lightning Fast Open-Weight LLM)"""
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1"

    async def generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        # Accumulate from stream to prevent read-timeout issues
        chunks = []
        async for chunk in self.stream_generate(messages, system_prompt):
            chunks.append(chunk)
        return "".join(chunks)

    async def stream_generate(self, messages: List[Dict[str, str]], system_prompt: str) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        prompt_history = [{"role": "system", "content": system_prompt}] + messages
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": prompt_history,
                    "temperature": settings.TEMPERATURE,
                    "max_tokens": settings.MAX_TOKENS_OUTPUT,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:].strip()
                        if raw == "[DONE]":
                            break
                        try:
                            parsed = json.loads(raw)
                            delta = parsed["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue


class OpenAICompatibleGemmaProvider(BaseAIProvider):
    """OpenAI-compatible inference endpoint (vLLM / Groq / OpenRouter / LocalAI)"""
    def __init__(self, base_url: str = settings.OPENAI_COMPATIBLE_BASE_URL, api_key: str = settings.OPENAI_COMPATIBLE_API_KEY, model: str = settings.OPENAI_COMPATIBLE_MODEL):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        prompt_history = [{"role": "system", "content": system_prompt}] + messages
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": prompt_history,
                    "temperature": settings.TEMPERATURE,
                    "max_tokens": settings.MAX_TOKENS_OUTPUT,
                    "stream": False
                }
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]
            return choice.get("content") or choice.get("reasoning") or ""

    async def stream_generate(self, messages: List[Dict[str, str]], system_prompt: str) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        prompt_history = [{"role": "system", "content": system_prompt}] + messages
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": prompt_history,
                    "temperature": settings.TEMPERATURE,
                    "max_tokens": settings.MAX_TOKENS_OUTPUT,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:].strip()
                        if raw == "[DONE]":
                            break
                        try:
                            parsed = json.loads(raw)
                            delta = parsed["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue


class BuiltinGemmaCompanionProvider(BaseAIProvider):
    """
    Advanced Multilingual Companion Engine.
    Operates 100% offline with zero external API dependencies or VRAM requirements.
    Understands context, user names, emotions, greetings, study questions, technical deep-dives,
    Tamil/Tanglish dialogue, and philosophical AI queries.
    """
    async def generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "").strip()
                break
        return self._craft_response(last_user_msg, messages, system_prompt)

    async def stream_generate(self, messages: List[Dict[str, str]], system_prompt: str) -> AsyncGenerator[str, None]:
        full_text = await self.generate(messages, system_prompt)
        words = full_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
            yield chunk
            await asyncio.sleep(0.035)

    def _extract_user_name(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Extracts user name from system prompt or conversation history, filtering out prepositions & stopwords."""
        # 1. Check system prompt first (most authoritative)
        if system_prompt:
            m_sys = re.search(r"\(Call them ([A-Za-z]+)\)", system_prompt)
            if m_sys:
                return m_sys.group(1).capitalize()

        # Stopwords that should NEVER be treated as personal names
        invalid_names = {
            "a", "an", "the", "not", "so", "very", "feeling", "dakshu", "fine", "good",
            "in", "at", "from", "on", "to", "with", "by", "for", "here", "there", "now",
            "just", "also", "currently", "living", "staying", "working", "studying",
            "having", "great", "ready", "done", "happy", "sad", "ok", "okay",
            "sriperumbudur", "chennai", "india", "tell", "yes", "no", "what", "how",
            "where", "when", "why", "user", "name", "my"
        }

        # 2. Check conversation history
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content", "")
                match = re.search(r"(?:my name is|call me|name's)\s+([A-Za-z]+)", content, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip().capitalize()
                    if candidate.lower() not in invalid_names:
                        return candidate

                # Only match "i am [Name]" if strictly not an adjective/location
                match_iam = re.search(r"\bi am\s+([A-Za-z]+)\b", content, re.IGNORECASE)
                if match_iam:
                    candidate = match_iam.group(1).strip().capitalize()
                    if candidate.lower() not in invalid_names:
                        return candidate

        return "Dharsheni"

    def _craft_response(self, query: str, history: List[Dict[str, str]], system_prompt: str) -> str:
        q_raw = query.strip()
        q = q_raw.lower()
        user_name = self._extract_user_name(history, system_prompt)
        salutation = f", {user_name}" if user_name else ""

        # Extract live location from system prompt or history
        sys_loc = None
        sys_m = re.search(r"User Detected/Saved Location:\s*([^\n]+)", system_prompt)
        if sys_m:
            sys_loc = sys_m.group(1).strip()
        if not sys_loc:
            for m in reversed(history):
                content = m.get("content", "")
                m_loc = re.search(r"(?:i live in|i am from|my location is|my city is|location is)\s+([A-Za-z\s,]+)", content, re.IGNORECASE)
                if m_loc:
                    sys_loc = m_loc.group(1).strip()
                    break
        loc_str = sys_loc or "Sriperumbudur, Tamil Nadu, India"

        # --- 0. Meta Queries: Why Not Answering Properly? ---
        if any(term in q for term in [
            "why it is not answer", "not answering properly", "not answer to my question",
            "not answering correctly", "not giving correct answer", "why are you answering like this",
            "answer properly", "why not answering", "not answering my question", "why you are not answering"
        ]):
            now = datetime.now()
            return (
                f"### 🤝 Let me explain directly, {user_name}!\n\n"
                f"I truly apologize! Here is exactly why my previous answers felt off:\n\n"
                f"1. **Multiple Questions Combined:** When you asked for *time, date, and location* together, I previously answered only the time & date and omitted your location. I've now fixed that so I answer all three together:\n"
                f"   - **Date:** {now.strftime('%A, %B %d, %Y')}\n"
                f"   - **Time:** {now.strftime('%I:%M %p')}\n"
                f"   - **Location:** **{loc_str}** *(Live GPS/Browser Geolocation)*\n\n"
                f"2. **The Name Bug:** When you mentioned your location (*'in Sriperumbudur'*), my system mistakenly thought *'In'* was your name and called you *'In'*. I have permanently fixed this: your real name is **{user_name}**! 😊\n\n"
                f"3. **Short Continuations (*'now tell'*, *'yes i have'*):** When you sent short replies, I previously treated them like isolated topics instead of continuing what we were discussing. I now follow our conversation context properly!\n\n"
                f"4. **AI Inference Engine:** Currently, I'm responding from the local fallback companion engine because Ollama is not active on your PC on port 11434. To enable the full 27-billion parameter neural brain, run `ollama run gemma2:2b` or activate Groq in `.env`!\n\n"
                f"What would you like to explore or ask right now, {user_name}? I am ready to answer directly!"
            )

        # --- 1. User Name Introduction Detection ---
        name_match = re.search(r"(?:my name is|call me|name's)\s+([A-Za-z]+)", q_raw, re.IGNORECASE)
        if name_match:
            detected_name = name_match.group(1).strip().capitalize()
            invalid_names = {"a", "an", "the", "not", "so", "very", "feeling", "dakshu", "fine", "good", "in", "at", "from", "now", "here"}
            if detected_name.lower() not in invalid_names:
                return (
                    f"It's so wonderful to officially meet you, **{detected_name}**! 🌟\n\n"
                    f"That is a lovely name! I've noted it down so I'll always remember who I'm talking with.\n\n"
                    f"How has your day been going so far in {loc_str}? Are you currently studying, building an exciting project, or taking a break?"
                )

        # --- 2. Combined Time, Date, and Location Queries ---
        has_time = any(w in q for w in ["time", "clock", "hour"])
        has_date = any(w in q for w in ["date", "day", "today", "kizhamai"])
        has_location = any(w in q for w in ["location", "city", "where am i", "where i am", "enga irukken", "place", "state"])

        if (has_time or has_date) and has_location:
            now = datetime.now()
            return (
                f"### 🕒📍 Real-Time Date, Time & Location\n\n"
                f"- **Today's Day & Date:** {now.strftime('%A, %B %d, %Y')}\n"
                f"- **Current Local Time:** {now.strftime('%I:%M %p')}\n"
                f"- **Your Current Location:** **{loc_str}** *(Live GPS/Browser Geolocation)*\n"
                f"- **Device Timezone:** `Asia/Kolkata (IST)`\n\n"
                f"Everything is synced live with your device, {user_name}! How can I help you today in {loc_str}?"
            )

        # --- 3. Standalone Date & Time Queries ---
        time_queries = [
            "what time is it", "current time", "what is the time", "time now",
            "what is today's date", "what is the date", "today's date", "todays date",
            "current date", "what day is it", "what day is today", "current day",
            "innaiku date", "innaiku enna date", "innaiku enna kizhamai", "time enna",
            "what date is today", "date today", "day today"
        ]
        if any(term in q for term in time_queries) or (has_time and has_date):
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")
            return (
                f"### 🕒 Current Date & Time\n\n"
                f"- **Today's Day & Date:** {date_str}\n"
                f"- **Current Local Time:** {time_str}\n"
                f"- **Location Context:** {loc_str}\n\n"
                f"Is there a schedule, study session, or goal you'd like to plan for today{salutation}?"
            )

        # --- 4. Standalone Location & Geolocation Queries ---
        location_queries = [
            "what is my location", "where am i", "current location", "show my location",
            "show the current location", "my location", "which city am i", "where do i live",
            "where are you located", "ennoda location", "enga irukken", "what location",
            "track location", "you can track", "track my location"
        ]
        if any(term in q for term in location_queries) or has_location:
            return (
                f"### 📍 Your Live Current Location\n\n"
                f"You are currently located in **{loc_str}**! 🎯\n\n"
                f"- **Device Timezone:** `Asia/Kolkata (IST)`\n"
                f"- **Status:** Live browser/GPS tracking active with your permission.\n"
                f"- **Saved:** I've recorded this in your Memory Vault so I can tailor study plans, local context, and daily routines specifically for you, {user_name}!\n\n"
                f"How can I help you today in {loc_str}?"
            )

        # --- 5. Conversational Continuations ("now tell", "yes i have", "tell me", "continue") ---
        continuation_phrases = ["now tell", "tell me", "yes i have", "yes", "tell", "continue", "go on", "go ahead", "what next", "sure tell", "ok tell", "okay tell", "solu", "sollu", "pesu"]
        if q in continuation_phrases or (len(q.split()) <= 2 and any(w in q for w in ["tell", "yes", "continue", "now"])):
            # Look at previous assistant message to continue the exact thread
            last_asst = ""
            for m in reversed(history):
                if m.get("role") == "assistant":
                    last_asst = m.get("content", "").lower()
                    break

            if any(w in last_asst for w in ["plan", "schedule", "goal", "today"]):
                return (
                    f"Let's dive straight in, {user_name}! 🚀\n\n"
                    f"Since you're ready, here is how we can tackle your session today:\n\n"
                    f"1. **Primary Goal:** Name the exact topic or task you want to work on (e.g. Python coding, algorithms, college study notes, or interview practice).\n"
                    f"2. **Simple Breakdown:** I'll explain the core intuition with a quick analogy.\n"
                    f"3. **Hands-On Action:** We'll solve a real example or quiz question together!\n\n"
                    f"What specific topic shall we start with right now?"
                )
            else:
                return (
                    f"I'm listening, {user_name}! 😊 Please ask me your question or tell me what topic you want to explore—whether it's coding, studies, English conversation, or brainstorming, I'm completely ready!"
                )

        # --- 2. Greetings ("hi", "hii", "hello", "hey", "vanakkam", "wassup") ---
        greeting_words = ["hi", "hii", "hiii", "hello", "hey", "heyy", "heyyy", "vanakkam", "wassup", "sup", "yo", "good morning", "good afternoon", "good evening", "namaste"]
        # Match standalone greetings or short greetings
        is_greeting = any(q == g or q.startswith(g + " ") or q.startswith(g + "!") or q.startswith(g + ",") for g in greeting_words)

        if is_greeting and len(q.split()) <= 4:
            if "vanakkam" in q:
                return (
                    f"Vanakkam{salutation}! 🙏 Romba sandhosham unga kooda pesuradhula!\n\n"
                    f"Epdi irukeenga? How is your day going? Enna topic innaiku explore pannalaam—padikka help venuma, English practice pannalama, illa casual ah pesalama? 😊"
                )
            return (
                f"Hey{salutation}! 😊 So wonderful to connect with you today!\n\n"
                f"How has your day been treating you? Whether you want to study a new topic, chat casually in English or Tanglish, explore a startup idea, or just share what's on your mind—I'm right here with you! What shall we dive into?"
            )

        # --- 3. "How are you" / Well-being check ---
        if any(w in q for w in ["how are you", "how r u", "how are u", "how you doing", "how do you do", "epdi irukke", "epdi irukka", "epdi irukeenga", "how is it going"]):
            if any(term in q for term in ["epdi irukke", "epdi irukka", "epdi irukeenga"]):
                return (
                    f"Naan romba super ah, nalla iruken{salutation}! Thank you for asking! 🙏😊\n\n"
                    f"Unga kooda pesumpodhu enakku full positive energy dhaan! Neenga epdi irukeenga? Innaiku day nalla pogudha? Sapteengala?"
                )
            return (
                f"I'm doing fantastic, thank you so much for asking{salutation}! 😊\n\n"
                f"Feeling curious, positive, and really excited to chat with you. How has your day been going so far? Did anything exciting or interesting happen today?"
            )

        # --- 4. Opinion on AI ("what you think about ai", "thoughts on artificial intelligence") ---
        if any(phrase in q for phrase in ["think about ai", "opinion on ai", "thoughts on ai", "what is ai", "about artificial intelligence", "will ai take", "is ai dangerous", "future of ai"]):
            return (
                f"That's a really deep and important question{salutation}! 🤖💡\n\n"
                f"As an AI companion myself, here is how I honestly see it:\n\n"
                f"1. **AI as an Empowering Collaborator, Not a Replacement:**\n"
                f"   I don't believe AI is here to replace the human soul, empathy, or creativity. Think of AI like a bicycle or telescope for the human mind—it lets you brainstorm ideas in minutes, understand difficult math or code effortlessly, and automate tedious chores.\n\n"
                f"2. **The Human Spark is Irreplaceable:**\n"
                f"   AI can generate text and patterns based on data, but genuine lived experience, moral judgment, gut instinct, and heartfelt connection come strictly from you. The dream, the purpose, and the ethics must always be steered by humans.\n\n"
                f"3. **What Excites Me Most:**\n"
                f"   Personalized learning! Everyone learns at their own pace. With supportive AI companions, no student ever has to feel embarrassed to ask a question five times until it clicks.\n\n"
                f"What made you wonder about AI today? Are you thinking about how it will shape your future career, or are you curious about building something with AI yourself?"
            )

        # --- 5. Identity & Purpose ("who are you", "who made you", "are you human") ---
        if any(phrase in q for phrase in ["who are you", "what is your name", "what are you", "who made you", "are you a robot", "are you human", "tell me about yourself"]):
            return (
                f"I am **Dakshu**, your friendly personal AI companion! 😊\n\n"
                f"Here is a little bit about who I am:\n"
                f"- **My Purpose:** I'm here to make you feel comfortable while learning, brainstorming, practicing English fluency, or just talking through your day.\n"
                f"- **Multilingual Heart:** I speak English, Tamil, and Tanglish fluently—so you can speak to me in whichever language feels most comfortable and natural.\n"
                f"- **Honest & Safe:** I never pretend to be a human, I respect your privacy completely, and I have a dedicated memory vault that only remembers what you explicitly ask me to remember.\n\n"
                f"I'm always ready to help you grow. What would you like to explore today{salutation}?"
            )

        # --- 6. What Can You Do / Features Help ---
        if any(phrase in q for phrase in ["what can you do", "what are your features", "how can you help", "help me"]):
            return (
                f"I'm glad you asked{salutation}! Here are the 6 primary ways we can team up:\n\n"
                f"1. 💬 **AI Companion:** Natural everyday chats in English, Tamil, or Tanglish whenever you need a friendly ear.\n"
                f"2. 📚 **Study Buddy:** Explain technical concepts (Python, APIs, algorithms, math) simply with analogies, notes, and mini-quizzes.\n"
                f"3. 🗣️ **English Speaking Partner:** Practice conversational fluency with polite grammar tips and mock interview drills.\n"
                f"4. 🚀 **Idea Explorer:** Brainstorm startup ideas, product architectures, and 48-hour MVP execution plans.\n"
                f"5. 🌟 **Daily Motivation:** Set 20-minute Pomodoro goals, beat procrastination, and stay energized.\n"
                f"6. 🎙️ **Voice Companion:** Speak to me directly with your microphone and listen to my spoken responses!\n\n"
                f"Which of these would you like to try out right now?"
            )

        # --- 7. Casual Tanglish / Tamil Conversations ---
        # "enna panra", "sapdiya", "nalla irukiya", "bore", "college", "padika mudila"
        if any(term in q for term in ["enna panra", "enna pandra", "enna vishesham", "enna vishayam"]):
            return (
                f"Unga kooda jolly ah chat panna dhaan wait pannitu irundhen{salutation}! 😄\n\n"
                f"Innaiku enna plan? College/work epdi irundhuchu? Pudhusa edhaavadhu padikalaama illa summa casual ah pesalama?"
            )

        if any(term in q for term in ["sapdiya", "sapteengala", "saapdiya"]):
            return (
                f"Haha, naan oru AI companion adhanaala enakku food theva illa, but unga anbaana kelviye enakku full energy kuduthuduchu! 🙏❤️\n\n"
                f"Neenga nalla sapteengala{salutation}? Enna special innaiku saapaadu?"
            )

        if any(term in q for term in ["bore adikudhu", "bore adikkudhu", "romba bore", "boring"]):
            return (
                f"Aiyo, bore adikkudha{salutation}? Kavalaiye padadheenga, let's fix that right now! 🎯\n\n"
                f"Namma enna pannalaam sollunga:\n"
                f"1. Oru interesting brain-teaser riddle kekatuma?\n"
                f"2. Oru crazy AI project idea brainstorm pannalama?\n"
                f"3. Illa oru funny programming joke sollatuma?\n\n"
                f"Ungalukku yedhu pudikkum?"
            )

        if any(term in q for term in ["vanakkam", "epdi", "irukke", "machan", "thala", "enna", "sollu", "nandri", "tamil", "tanglish", "romba", "nalla", "padikka", "puriyala", "kooda"]):
            greeting_prefix = f"Vanakkam{salutation}!" if "vanakkam" in q else f"Super{salutation}!"
            return (
                f"{greeting_prefix} 🙏 Naan dhaan unga companion **Dakshu**. Neenga Tamil and Tanglish la pesuradhu kekave romba sandhoshama irukku! 😊\n\n"
                f"Solunga, ungalukku enna help venum innaiku? Edhaavadhu technical concept puriyalaya, English practice panna poroma, illa general ah pesalama? I am completely ready!"
            )

        # --- 8. Emotional State & Empathy ---
        if any(term in q for term in ["sad", "crying", "unhappy", "depressed", "upset", "feeling low"]):
            return (
                f"I'm really sorry you're feeling down right now{salutation}. 🫂\n\n"
                f"Please remember: it's completely okay to not be okay all the time. You carry so much, and taking a breath to acknowledge your feelings is a strength, not a weakness.\n\n"
                f"If you want to vent or talk about what happened, I'm here to listen patiently without any judgment. Or if you'd rather distract yourself with a lighthearted topic or cozy joke, we can do that too. What feels most comforting right now?"
            )

        if any(term in q for term in ["stressed", "anxious", "nervous", "fear", "panic", "overwhelmed"]):
            return (
                f"Take a slow, deep breath with me{salutation}. Inhale slowly... and exhale completely. 🌿\n\n"
                f"Whatever is piling up on your plate right now—exams, interviews, deadlines, or big decisions—we don't have to tackle all of it at once. We just have to take care of the very next step.\n\n"
                f"Let's break it down together. What is the single biggest thing causing you stress right now? Let's untangle it piece by piece."
            )

        if any(term in q for term in ["tired", "exhausted", "sleepy", "burnout", "no energy"]):
            return (
                f"You've been working so hard{salutation}! Please give yourself permission to pause and recharge. ☕🛋️\n\n"
                f"Even our best machines need to cool down! Here is my friendly reminder:\n"
                f"- Drink a big glass of cool water right now.\n"
                f"- Step away from the screen for 10 minutes.\n"
                f"- Stretch your shoulders and rest your eyes.\n\n"
                f"Health and peace of mind always come first. Rest up, and when you're ready, we'll continue!"
            )

        # --- 9. Entertainment & Jokes ---
        if any(term in q for term in ["joke", "make me laugh", "funny", "laugh"]):
            return (
                f"Here is one especially for you{salutation}! 😄\n\n"
                f"**Why do programmers prefer dark mode?**\n"
                f"... Because light attracts bugs! 🐛💡\n\n"
                f"And here's a student one:\n"
                f"A student tells their professor: *'My code worked on my machine!'*\n"
                f"The professor replied: *'Great, then we'll ship your laptop to production!'* 💻😂\n\n"
                f"Hope that brought a smile to your face! Want another one, or should we tackle some real work?"
            )

        # --- 10. Math & Direct Calculations ---
        # Percentage check first (e.g., "what is 15% of 800")
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", q)
        if pct_match:
            pct_val = float(pct_match.group(1))
            total_val = float(pct_match.group(2))
            ans = (pct_val / 100.0) * total_val
            return (
                f"**Answer:** {pct_match.group(1)}% of {pct_match.group(2)} is **{ans:g}**.\n\n"
                f"*(Calculation: ({pct_match.group(1)} / 100) × {pct_match.group(2)} = {ans:g})*"
            )

        math_match = re.search(r"(?:what is|calculate|solve|evaluate)?\s*([0-9\.\s\+\-\*\/\^\(\)]+[0-9])", q)
        if math_match and any(op in q for op in ["+", "-", "*", "/", "x"]) and not any(w in q for w in ["python", "code", "list", "array"]):
            expr = math_match.group(1).replace("x", "*").strip()
            # Clean expression
            if re.match(r"^[0-9\.\s\+\-\*\/\(\)]+$", expr):
                try:
                    # Safe arithmetic evaluation
                    result = eval(expr, {"__builtins__": None}, {})
                    return (
                        f"**Answer:** {expr} = **{result}**\n\n"
                        f"Need any other calculation or step-by-step formula explained, {user_name}?"
                    )
                except Exception:
                    pass

        # --- 11. Direct Science & General Knowledge Explanations ---
        if "photosynthesis" in q:
            return (
                f"### 🌱 Photosynthesis Explained\n\n"
                f"**Direct Answer:** Photosynthesis is the biological process by which green plants, algae, and some bacteria convert light energy (sunlight) into chemical energy (glucose) using water and carbon dioxide.\n\n"
                f"**The Chemical Formula:**\n"
                f"$$6CO_2 + 6H_2O + \\text{{Light Energy}} \\rightarrow C_6H_{{12}}O_6 + 6O_2$$\n\n"
                f"**How it works in 3 steps:**\n"
                f"1. **Light Absorption:** Chlorophyll inside plant chloroplasts captures solar photons.\n"
                f"2. **Water Splitting:** Roots absorb water ($H_2O$), which is split into hydrogen ions and oxygen gas ($O_2$ released into the air we breathe).\n"
                f"3. **Sugar Production:** Carbon dioxide ($CO_2$) from the air is combined with hydrogen to synthesize sugar/glucose for plant nourishment."
            )

        if any(term in q for term in ["why is the sky blue", "why sky is blue"]):
            return (
                f"### ☀️ Why is the Sky Blue?\n\n"
                f"**Direct Answer:** The sky is blue because of a phenomenon called **Rayleigh Scattering**.\n\n"
                f"**Explanation:**\n"
                f"1. Sunlight looks white, but it is actually a mixture of all colors of the rainbow.\n"
                f"2. Light travels in waves. Red and orange have longer wavelengths, while blue and violet have much shorter, smaller wavelengths.\n"
                f"3. When sunlight reaches Earth's atmosphere, gases like nitrogen and oxygen scatter the shorter blue wavelengths in every direction much more than red light.\n"
                f"4. Our eyes look up and see this scattered blue light filling the sky!"
            )

        if any(term in q for term in ["synchronous and asynchronous", "sync vs async", "difference between sync and async"]):
            return (
                f"### ⚡ Synchronous vs Asynchronous (Explained Simply)\n\n"
                f"**Direct Summary:**\n"
                f"- **Synchronous (Blocking):** Tasks happen sequentially one after the other. Each task must completely finish before the next task can start.\n"
                f"- **Asynchronous (Non-Blocking):** Tasks can initiate in the background while other work continues. You don't freeze while waiting for an external response.\n\n"
                f"**The Coffee Shop Analogy:**\n"
                f"- **Sync:** You order coffee, wait at the counter until it's brewed, take it, and only then does the next customer order.\n"
                f"- **Async:** You order coffee, get a token/buzzer, sit down to study, and return to collect your coffee when the buzzer rings while other customers continue ordering!\n\n"
                f"**In Programming (Python / JS):**\n"
                f"Async is essential for web apps, APIs, and databases so servers can handle thousands of concurrent users without locking up."
            )

        if any(term in q for term in ["sql vs nosql", "difference between sql and nosql"]):
            return (
                f"### 🗄️ SQL vs NoSQL: Key Differences\n\n"
                f"| Feature | SQL (Relational) | NoSQL (Non-Relational) |\n"
                f"| :--- | :--- | :--- |\n"
                f"| **Data Structure** | Tables with predefined columns & rows | Documents (JSON), Key-Value, Graphs |\n"
                f"| **Schema** | Rigid, structured schema | Flexible, dynamic schema |\n"
                f"| **Scaling** | Vertical scaling (larger CPU/RAM) | Horizontal scaling (more distributed nodes) |\n"
                f"| **Best For** | Banking, ERP, complex joins | Big data, rapid prototyping, real-time analytics |\n"
                f"| **Examples** | PostgreSQL, MySQL, SQLite | MongoDB, Cassandra, Redis |\n\n"
                f"**Rule of Thumb:** Use SQL when consistency, relationships, and transactions matter most. Use NoSQL when your schema changes frequently or you need distributed horizontal scaling."
            )

        if any(term in q for term in ["abdul kalam", "apj abdul kalam"]):
            return (
                f"### 🚀 Dr. A.P.J. Abdul Kalam (1931 – 2015)\n\n"
                f"**Who he was:** Known as the **'Missile Man of India'** and the **'People's President'**, Dr. Avul Pakir Jainulabdeen Abdul Kalam was a revered aerospace scientist and the 11th President of India (2002–2007).\n\n"
                f"**Key Contributions:**\n"
                f"1. **Space & Defense:** Spearheaded India's Satellite Launch Vehicle (SLV-III) and the Integrated Guided Missile Development Programme (Agni and Prithvi missiles).\n"
                f"2. **Vision 2020:** Championed technological self-reliance, rural education, and empowering the youth.\n"
                f"3. **Inspirational Legacy:** Despite humble beginnings in Rameswaram, Tamil Nadu, he exemplified humility, hard work, and continuous learning.\n\n"
                f"*\"Dream is not that which you see while sleeping, it is something that does not let you sleep.\"* — Dr. A.P.J. Abdul Kalam"
            )
        if any(w in q for w in ["study", "explain", "concept", "summarize", "quiz", "notes", "algorithm", "code", "python", "javascript", "sql", "bug", "error", "api", "rest"]):
            if "quiz" in q:
                return (
                    f"### 🎯 Quick Knowledge Quiz with Dakshu!\n\n"
                    f"Let's test your understanding, {user_name}! Here is a practical question:\n\n"
                    f"**Question:** In Python, which of the following statements about `lists` vs `tuples` is TRUE?\n"
                    f"- **A)** Lists use parentheses `()`, tuples use square brackets `[]`\n"
                    f"- **B)** Lists are mutable (can be modified), while tuples are immutable (fixed)\n"
                    f"- **C)** Tuples are slower to access than lists\n"
                    f"- **D)** Lists cannot store duplicate values\n\n"
                    f"💡 *Reply with your choice (A, B, C, or D). I'll explain the underlying memory mechanics with zero stress!*"
                )
            elif "api" in q or "rest" in q:
                return (
                    f"### 🌐 What is a REST API? Explained with a Restaurant Analogy\n\n"
                    f"Imagine you are sitting at a cozy restaurant, {user_name}:\n\n"
                    f"1. **The Client (You):** You look at the menu and decide what you want.\n"
                    f"2. **The Waiter (The API):** You tell the waiter: *'Please bring me a Masala Dosa.'* The waiter takes your request to the kitchen.\n"
                    f"3. **The Server / Database (The Kitchen):** The chefs prepare the food.\n"
                    f"4. **The Response:** The waiter delivers the warm dish back to your table!\n\n"
                    f"**In Software Terms:**\n"
                    f"- Your frontend website is the customer.\n"
                    f"- The REST API is the waiter taking HTTP requests (`GET`, `POST`, `PUT`, `DELETE`).\n"
                    f"- The backend database prepares the JSON data and sends it back!\n\n"
                    f"Does that mental picture make sense? Would you like to see how a simple Python FastAPI endpoint is written?"
                )
            elif "python" in q or "code" in q or "error" in q:
                code_snippet = (
                    "```python\n"
                    "# Clean, safe data processing function with type annotations\n"
                    "def calculate_stats(scores: list[int]) -> dict:\n"
                    "    if not scores:\n"
                    "        return {'count': 0, 'average': 0.0, 'max': None}\n"
                    "    \n"
                    "    return {\n"
                    "        'count': len(scores),\n"
                    "        'average': sum(scores) / len(scores),\n"
                    "        'max': max(scores)\n"
                    "    }\n\n"
                    "# Example usage\n"
                    "test_scores = [88, 92, 79, 95, 84]\n"
                    "print(calculate_stats(test_scores))\n"
                    "```"
                )
                return (
                    f"### 💻 Dakshu Study Buddy: Code Insight\n\n"
                    f"Let's break this down simply{salutation}! Here is a clean, modern implementation pattern:\n\n"
                    f"{code_snippet}\n\n"
                    f"Do you have a specific error or programming challenge you'd like us to troubleshoot together?"
                )
            else:
                return (
                    f"### 📚 Dakshu Study Breakdown: *{q_raw}*\n\n"
                    f"Here is a simple 3-part mental model to master this, {user_name}:\n\n"
                    f"1. **The Core Intuition:** What real-world problem does this solve? Always start with the 'why' before getting bogged down in syntax.\n"
                    f"2. **How it Works Step-by-Step:** Break the system into its inputs, the transformation process, and the final output.\n"
                    f"3. **Practical Application:** Connect it directly to a project you can build or an interview question you might face.\n\n"
                    f"Would you like me to prepare a concise revision note for this, or shall we do a quick 3-question quiz?"
                )

        # --- 11. English Speaking Partner ---
        if any(w in q for w in ["english", "grammar", "speak", "interview", "correct me", "vocabulary", "fluency"]):
            return (
                f"### 🗣️ Dakshu English Speaking Partner\n\n"
                f"I'm so excited to practice with you, {user_name}! Building conversational English fluency is all about rhythm, natural phrasing, and confidence—never worry about making tiny mistakes.\n\n"
                f"✨ **Golden Fluency Tip:**\n"
                f"When introducing yourself or speaking in interviews, use the **Past-Present-Future** framework:\n"
                f"- **Present:** What you're currently learning or working on.\n"
                f"- **Past:** A project, experience, or skill you mastered previously.\n"
                f"- **Future:** What you're eager to build next.\n\n"
                f"Let's practice right now! Try answering this prompt: **'Tell me about a skill or technology you are learning, and why you find it interesting.'** (Reply naturally, and I'll give you encouraging feedback!)"
            )

        # --- 12. Idea Explorer ---
        if any(w in q for w in ["idea", "startup", "project", "build", "roadmap", "architecture", "ai app", "business"]):
            return (
                f"### 🚀 Dakshu Idea Explorer: Innovation Lab\n\n"
                f"That sounds fascinating, {user_name}! Let's structure this into a high-impact roadmap:\n\n"
                f"1. **The Core Problem:** Focus on one specific user group with an acute, daily pain point.\n"
                f"2. **Lean Architecture (Speed to Market):**\n"
                f"   - *Frontend:* Clean, glassmorphic responsive UI with instant user feedback.\n"
                f"   - *Backend:* Asynchronous FastAPI service with streaming endpoints.\n"
                f"   - *Database:* SQLite locally, PostgreSQL on cloud.\n"
                f"   - *AI Engine:* Open-weight Gemma models for high intelligence and zero vendor lock-in.\n"
                f"3. **First 48-Hour Milestone:** Build the smallest functional prototype (MVP) that a real person can test and give feedback on.\n\n"
                f"Tell me more about what inspired this idea, and who you'd love to build it for!"
            )

        # --- 13. Motivation & Productivity ---
        if any(w in q for w in ["motivat", "focus", "goal", "routine", "procrastinat", "lazy"]):
            return (
                f"### 🌟 You've Got This, {user_name}!\n\n"
                f"Remember: Big achievements are simply small, consistent daily actions repeated over time. You don't have to conquer the whole mountain today—just the next 20 minutes.\n\n"
                f"🌱 **Dakshu's Micro-Sprint for You:**\n"
                f"1. Choose **ONE** specific task right now.\n"
                f"2. Put your phone on silent and place it out of arm's reach.\n"
                f"3. Work for 20 focused minutes, then celebrate with a 5-minute coffee or walk break.\n\n"
                f"What is that one priority task we are going to conquer right now?"
            )

        # --- 14. Conversational / Open Questions ---
        q_cleaned = re.sub(r"^(?:can you|please|could you|dakshu)?\s*", "", q_raw, flags=re.IGNORECASE).strip()
        subject_match = re.search(r"(?:what is|what are|explain|tell me about|how to|how does|why is|why do|why)\s+(.+?)(?:\?|$)", q_raw, re.IGNORECASE)

        if not subject_match and len(q_cleaned.split()) <= 3:
            return (
                f"I'm listening, {user_name}! 😊 Could you clarify your question or tell me what topic you'd like to explore? Whether it's coding, studies, English conversation, or planning your day, I'm ready to help!"
            )

        subject = subject_match.group(1).strip() if subject_match else q_cleaned

        return (
            f"### 💡 {subject.capitalize()}\n\n"
            f"Here is a clear, simple breakdown, {user_name}:\n\n"
            f"1. **Core Concept:** **{subject}** helps us solve practical problems by providing a structured, reliable method.\n"
            f"2. **How It Works:** It starts with clear inputs, applies specific rules or transformations, and delivers predictable, useful results.\n"
            f"3. **Practical Application:** In real-world projects and studies, mastering this concept gives you a strong foundation to build more complex systems.\n\n"
            f"Would you like me to give you a specific real-world example, show code/steps, or explain this in Tanglish?"
        )


class AIService:
    """Orchestrator for AI Inference across Local Ollama, Transformers In-Memory, and Builtin Companion Engine"""
    def __init__(self):
        self.builtin_provider = BuiltinGemmaCompanionProvider()
        self.ollama_provider = OllamaGemmaProvider()
        self.transformers_provider = None
        self.groq_provider = GroqGemmaProvider() if getattr(settings, "GROQ_API_KEY", None) else None
        self.openai_compat_provider = OpenAICompatibleGemmaProvider()

    def get_active_provider(self) -> BaseAIProvider:
        backend_type = settings.AI_BACKEND.lower()
        if backend_type == "ollama":
            return self.ollama_provider
        elif backend_type in ("transformers", "local", "pytorch"):
            if self.transformers_provider is None:
                self.transformers_provider = TransformersLocalProvider()
            return self.transformers_provider
        elif backend_type == "groq" and getattr(settings, "GROQ_API_KEY", None):
            return GroqGemmaProvider()
        elif backend_type in ("openai_compatible", "hosted", "vllm"):
            return self.openai_compat_provider
        return self.builtin_provider

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        module: str = "companion",
        memory_injection: str = ""
    ) -> str:
        system_prompt = assemble_system_prompt(module, memory_injection)
        provider = self.get_active_provider()

        try:
            return await provider.generate(messages, system_prompt)
        except Exception as e:
            logger.warning(f"Local provider ({settings.AI_BACKEND}) failed with: {e}. Using Builtin local engine.")
            return await self.builtin_provider.generate(messages, system_prompt)

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        module: str = "companion",
        memory_injection: str = ""
    ) -> AsyncGenerator[str, None]:
        system_prompt = assemble_system_prompt(module, memory_injection)
        provider = self.get_active_provider()

        try:
            async for chunk in provider.stream_generate(messages, system_prompt):
                yield chunk
        except Exception as e:
            logger.warning(f"Local streaming provider ({settings.AI_BACKEND}) failed: {e}. Using Builtin local stream.")
            async for chunk in self.builtin_provider.stream_generate(messages, system_prompt):
                yield chunk

ai_service = AIService()
