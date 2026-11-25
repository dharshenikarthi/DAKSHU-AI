/**
 * DAKSHU AI - Chat Application Controller
 * Handles streaming AI chat, conversation threads, voice companion, and 3D orb integration.
 */

class DakshuChatController {
  constructor() {
    this.activeConversationId = null;
    this.conversations = [];
    this.activeModule = 'companion';
    this.isGenerating = false;
    this.abortController = null;
    this.lastUserMessage = '';

    // DOM Elements
    this.messagesContainer = document.getElementById('chat-messages');
    this.chatTextarea = document.getElementById('chat-textarea');
    this.sendBtn = document.getElementById('chat-send-btn');
    this.voiceBtn = document.getElementById('voice-record-btn');
    this.stopBtn = document.getElementById('stop-generation-btn');
    this.sidebarConvs = document.getElementById('sidebar-conversations');
    this.newChatBtn = document.getElementById('new-chat-btn');
    this.companionStateText = document.getElementById('companion-state-text');

    // Visualizer & Voice
    this.orb = null;
    this.voice = null;

    this.init();
  }

  async init() {
    // 1. Auth check & Guest Mode configuration
    const isAuth = DakshuApp.isAuthenticated();
    if (!isAuth) {
      const nameEl = document.getElementById('sidebar-user-name');
      const badgeEl = document.getElementById('sidebar-user-badge');
      if (nameEl) nameEl.innerText = "Guest Mode";
      if (badgeEl) badgeEl.href = "login.html";

      if (this.sidebarConvs) {
        this.sidebarConvs.innerHTML = `
          <div style="padding: 1.5rem 0.8rem; text-align: center; color: var(--text-dim); font-size: 0.85rem; line-height: 1.5;">
            <i data-lucide="sparkles" style="width: 24px; height: 24px; color: var(--neon-cyan); margin-bottom: 8px;"></i>
            <div style="font-weight: 700; color: #ffffff; margin-bottom: 4px;">Guest Visitor</div>
            <p style="margin: 6px 0 12px; font-size: 0.8rem;">You can chat freely! To save chat history & memories:</p>
            <a href="login.html" class="btn btn-primary" style="display: inline-block; padding: 0.4rem 0.8rem; font-size: 0.8rem; width: 100%;">Log In / Sign Up</a>
          </div>
        `;
        if (window.lucide) window.lucide.createIcons();
      }
    }

    // 2. Initialize Mini 3D Companion Orb
    try {
      if (window.DakshuOrb) {
        this.orb = new window.DakshuOrb('mini-orb-container', { isMini: true });
      }
    } catch (e) {
      console.warn("Could not load 3D orb in mini canvas:", e);
    }

    // 3. Initialize Voice Engine
    if (window.DakshuVoice) {
      this.voice = new window.DakshuVoice(this.orb);
    }

    // 4. Bind Events
    this.bindEvents();

    // 5. Update local model status badge
    this.checkModelStatus();

    // 6. Detect and track live location with user permission
    this.detectAndTrackLocation();

    // 7. Load conversations if authenticated
    if (isAuth) {
      await this.loadConversationsList();
    }

    // 8. Check URL query params for module, starter prompt, and conversation ID
    const urlParams = new URLSearchParams(window.location.search);
    const modParam = urlParams.get('module');
    if (modParam) {
      this.switchModule(modParam);
    }

    const promptParam = urlParams.get('prompt');
    if (promptParam && this.chatTextarea) {
      this.chatTextarea.value = promptParam;
      this.chatTextarea.style.height = 'auto';
      this.chatTextarea.style.height = Math.min(this.chatTextarea.scrollHeight, 140) + 'px';
    }

    const convId = urlParams.get('id');
    if (convId && isAuth) {
      this.selectConversation(parseInt(convId));
    } else if (this.conversations.length > 0) {
      this.selectConversation(this.conversations[0].id);
    } else {
      this.renderWelcomeScreen();
    }
  }

  switchModule(mod) {
    if (!mod) return;
    const targetMod = mod.toLowerCase();
    const chip = document.querySelector(`.module-chip[data-module="${targetMod}"]`);
    if (chip) {
      document.querySelectorAll('.module-chip').forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      this.activeModule = targetMod;
      if (typeof DakshuApp !== 'undefined' && DakshuApp.showToast) {
        DakshuApp.showToast(`Switched mode to ${chip.innerText.trim()}`, 'info');
      }
    }
  }

  async checkModelStatus() {
    try {
      const resp = await DakshuApp.apiGet('/health');
      const badgeText = document.getElementById('local-model-name');
      if (badgeText && resp) {
        if (resp.ai_backend === 'ollama') {
          badgeText.textContent = `Local: ${resp.ai_model || 'Dakshu (Ollama)'}`;
        } else if (resp.ai_backend === 'transformers' || resp.ai_backend === 'local') {
          badgeText.textContent = `Local: Transformers`;
        } else {
          badgeText.textContent = `Local: Gemma Companion`;
        }
      }
    } catch (e) {
      console.warn("Could not fetch model status:", e);
    }
  }

  async detectAndTrackLocation() {
    const locBadge = document.getElementById('user-location-text');
    if (!locBadge) return;

    // Check cached location first for instant UI response
    const cachedLoc = localStorage.getItem('dakshu_user_location');
    if (cachedLoc) {
      this.userLocation = cachedLoc;
      const shortCity = cachedLoc.split(',')[0].trim();
      locBadge.textContent = shortCity || 'Location Set';
    }

    const updateUIWithLocation = (fullLoc, shortCity) => {
      this.userLocation = fullLoc;
      localStorage.setItem('dakshu_user_location', fullLoc);
      if (locBadge) locBadge.textContent = shortCity || fullLoc;
      const container = document.getElementById('user-location-badge');
      if (container) container.title = `Live Location: ${fullLoc} (Click to refresh)`;
    };

    const fetchReverseGeocode = async (lat, lon) => {
      try {
        const url = (lat !== undefined && lon !== undefined)
          ? `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`
          : `https://api.bigdatacloud.net/data/reverse-geocode-client`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          const city = data.city || data.locality || data.principalSubdivision || 'India';
          const parts = [city, data.principalSubdivision, data.countryName].filter(Boolean);
          const full = parts.join(', ');
          updateUIWithLocation(full, city);
          return true;
        }
      } catch (e) {
        console.warn("Reverse geocode fetch failed:", e);
      }
      return false;
    };

    // Try browser GPS with user permission
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          await fetchReverseGeocode(latitude, longitude);
        },
        async (err) => {
          console.log("GPS prompt declined or unavailable, falling back to IP location:", err.message);
          await fetchReverseGeocode();
        },
        { timeout: 7000, enableHighAccuracy: true }
      );
    } else {
      await fetchReverseGeocode();
    }
  }

  bindEvents() {
    // New chat button
    if (this.newChatBtn) {
      this.newChatBtn.addEventListener('click', () => this.startNewConversation());
    }

    // Send button
    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.handleSendMessage());
    }

    // Stop button
    if (this.stopBtn) {
      this.stopBtn.addEventListener('click', () => this.stopGeneration());
    }

    // Textarea enter & auto-expand
    if (this.chatTextarea) {
      this.chatTextarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSendMessage();
        }
      });

      this.chatTextarea.addEventListener('input', () => {
        this.chatTextarea.style.height = 'auto';
        this.chatTextarea.style.height = Math.min(this.chatTextarea.scrollHeight, 140) + 'px';
      });
    }

    // Voice record toggle
    if (this.voiceBtn && this.voice) {
      this.voiceBtn.addEventListener('click', () => this.handleVoiceToggle());
    }

    // Live location badge click to refresh
    const locBadge = document.getElementById('user-location-badge');
    if (locBadge) {
      locBadge.addEventListener('click', () => {
        DakshuApp.showToast("Updating live location...", "info");
        this.detectAndTrackLocation();
      });
    }

    // Module chips selector
    const moduleChips = document.querySelectorAll('.module-chip');
    moduleChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        moduleChips.forEach((c) => c.classList.remove('active'));
        chip.classList.add('active');
        this.activeModule = chip.dataset.module || 'companion';

        // Update greeting or companion prompt hint
        DakshuApp.showToast(`Switched mode to ${chip.innerText.trim()}`, 'info');
      });
    });

    // Mobile sidebar toggle
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.getElementById('chat-sidebar');
    if (mobileToggle && sidebar) {
      mobileToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
  }

  updateOrbState(state, text) {
    if (this.orb) {
      this.orb.setState(state);
    }
    if (this.companionStateText && text) {
      this.companionStateText.innerText = text;
    }
  }

  handleVoiceToggle() {
    if (!this.voice.isSupported()) {
      DakshuApp.showToast("Microphone speech recognition is not supported in this browser.", "error");
      return;
    }

    const isListening = this.voice.toggleListening(
      (transcript, isFinal) => {
        this.chatTextarea.value = transcript;
        if (isFinal) {
          this.handleSendMessage();
        }
      },
      (state) => {
        if (state === 'listening') {
          this.voiceBtn.classList.add('recording');
          this.updateOrbState('listening', 'Listening to you...');
        } else if (state === 'error') {
          this.voiceBtn.classList.remove('recording');
          this.updateOrbState('idle', 'Online • Ready');
          DakshuApp.showToast("Microphone input error or permission denied.", "error");
        } else {
          this.voiceBtn.classList.remove('recording');
          this.updateOrbState('idle', 'Online • Ready');
        }
      }
    );
  }

  async loadConversationsList() {
    try {
      const res = await DakshuApp.fetchWithAuth('/conversations');
      if (res.ok) {
        this.conversations = await res.json();
        this.renderSidebarConversations();
      }
    } catch (e) {
      console.error("Failed to load conversations:", e);
    }
  }

  renderSidebarConversations() {
    if (!this.sidebarConvs) return;

    if (this.conversations.length === 0) {
      this.sidebarConvs.innerHTML = `
        <div style="padding: 1.5rem 0.5rem; text-align: center; color: var(--text-dim); font-size: 0.85rem;">
          No conversations yet.<br>Say hi to Dakshu!
        </div>
      `;
      return;
    }

    this.sidebarConvs.innerHTML = this.conversations
      .map(
        (c) => `
        <div class="conversation-item ${c.id === this.activeConversationId ? 'active' : ''}" data-id="${c.id}">
          <i data-lucide="message-square" style="width: 15px; height: 15px; margin-right: 8px; flex-shrink: 0; color: var(--text-dim);"></i>
          <span class="conversation-item-title">${this.escapeHtml(c.title)}</span>
          <button class="conversation-delete-btn" title="Delete conversation" data-id="${c.id}">
            <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
          </button>
        </div>
      `
      )
      .join('');

    // Re-bind click events
    this.sidebarConvs.querySelectorAll('.conversation-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        if (e.target.closest('.conversation-delete-btn')) return;
        const id = parseInt(item.dataset.id);
        this.selectConversation(id);
      });
    });

    this.sidebarConvs.querySelectorAll('.conversation-delete-btn').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = parseInt(btn.dataset.id);
        if (confirm("Delete this conversation?")) {
          await this.deleteConversation(id);
        }
      });
    });

    if (window.lucide) window.lucide.createIcons();
  }

  async selectConversation(id) {
    this.activeConversationId = id;
    this.renderSidebarConversations();

    // Close mobile sidebar if open
    const sidebar = document.getElementById('chat-sidebar');
    if (sidebar) sidebar.classList.remove('open');

    try {
      const res = await DakshuApp.fetchWithAuth(`/conversations/${id}`);
      if (res.ok) {
        const data = await res.json();
        this.renderMessages(data.messages || []);
      }
    } catch (e) {
      console.error("Failed to load conversation details:", e);
    }
  }

  startNewConversation() {
    this.activeConversationId = null;
    this.renderSidebarConversations();
    this.renderWelcomeScreen();
  }

  async deleteConversation(id) {
    try {
      const res = await DakshuApp.fetchWithAuth(`/conversations/${id}`, { method: 'DELETE' });
      if (res.ok) {
        this.conversations = this.conversations.filter((c) => c.id !== id);
        if (this.activeConversationId === id) {
          if (this.conversations.length > 0) {
            this.selectConversation(this.conversations[0].id);
          } else {
            this.startNewConversation();
          }
        } else {
          this.renderSidebarConversations();
        }
        DakshuApp.showToast("Conversation deleted.", "info");
      }
    } catch (e) {
      DakshuApp.showToast("Failed to delete conversation.", "error");
    }
  }

  renderWelcomeScreen() {
    const user = DakshuApp.getUser();
    const firstName = user && user.full_name ? user.full_name.split(' ')[0] : 'friend';

    this.messagesContainer.innerHTML = `
      <div style="max-width: 650px; margin: auto; text-align: center; padding: 2rem 1rem;">
        <div style="width: 72px; height: 72px; border-radius: 20px; background: var(--gradient-primary); margin: 0 auto 1.5rem; display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-glow-purple);">
          <i data-lucide="sparkles" style="width: 36px; height: 36px; color: #ffffff;"></i>
        </div>
        <h2 style="font-size: 1.8rem; margin-bottom: 0.6rem;">Hey ${this.escapeHtml(firstName)}! I'm Dakshu 😊</h2>
        <p style="color: var(--text-muted); font-size: 1.05rem; margin-bottom: 2rem;">
          Your personal AI companion. English, Tamil, Tanglish—pesalaam! What shall we work on today?
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; text-align: left;">
          <div class="glass-card starter-card" data-prompt="Vanakkam Dakshu! How are you doing today? Epdi irukeenga?" style="cursor: pointer;">
            <div style="font-weight: 700; color: var(--neon-cyan); margin-bottom: 4px;">👋 Casual Companion</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">"Vanakkam Dakshu! How are you doing today? Epdi irukeenga?"</div>
          </div>
          <div class="glass-card starter-card" data-prompt="Explain how REST APIs work with a simple real-world analogy." style="cursor: pointer;">
            <div style="font-weight: 700; color: var(--neon-purple); margin-bottom: 4px;">📚 Study Buddy</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">"Explain how REST APIs work with a simple real-world analogy."</div>
          </div>
          <div class="glass-card starter-card" data-prompt="Let's practice an English interview question: Tell me about yourself." style="cursor: pointer;">
            <div style="font-weight: 700; color: var(--neon-blue); margin-bottom: 4px;">🗣️ English Practice</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">"Let's practice an English interview question: Tell me about yourself."</div>
          </div>
          <div class="glass-card starter-card" data-prompt="Give me a high-potential AI startup idea for college students." style="cursor: pointer;">
            <div style="font-weight: 700; color: var(--neon-emerald); margin-bottom: 4px;">🚀 Idea Explorer</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">"Give me a high-potential AI startup idea for college students."</div>
          </div>
        </div>
      </div>
    `;

    if (window.lucide) window.lucide.createIcons();

    // Starter card clicks
    this.messagesContainer.querySelectorAll('.starter-card').forEach((card) => {
      card.addEventListener('click', () => {
        const prompt = card.dataset.prompt;
        this.chatTextarea.value = prompt;
        this.handleSendMessage();
      });
    });
  }

  renderMessages(messages) {
    if (messages.length === 0) {
      this.renderWelcomeScreen();
      return;
    }

    this.messagesContainer.innerHTML = '';
    messages.forEach((msg) => {
      this.appendMessageToDOM(msg.role, msg.content, msg.id);
    });
    this.scrollToBottom();
  }

  appendMessageToDOM(role, content, messageId = null) {
    const isUser = role === 'user';
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${isUser ? 'user' : 'assistant'}`;

    const parsedContent = isUser ? this.escapeHtml(content).replace(/\n/g, '<br>') : this.parseMarkdown(content);

    wrapper.innerHTML = `
      <div class="message-avatar ${isUser ? 'user' : 'assistant'}">
        <i data-lucide="${isUser ? 'user' : 'sparkles'}" style="width: 18px; height: 18px;"></i>
      </div>
      <div class="message-bubble">
        <div class="message-text-content">${parsedContent}</div>
        ${
          !isUser
            ? `
          <div class="message-actions">
            <button class="msg-btn copy-msg-btn" title="Copy response">
              <i data-lucide="copy" style="width: 13px; height: 13px;"></i> Copy
            </button>
            <button class="msg-btn speak-msg-btn" title="Read aloud">
              <i data-lucide="volume-2" style="width: 13px; height: 13px;"></i> Speak
            </button>
            <button class="msg-btn regen-msg-btn" title="Regenerate">
              <i data-lucide="refresh-cw" style="width: 13px; height: 13px;"></i> Retry
            </button>
          </div>
        `
            : ''
        }
      </div>
    `;

    this.messagesContainer.appendChild(wrapper);

    // Bind action buttons
    if (!isUser) {
      const copyBtn = wrapper.querySelector('.copy-msg-btn');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => this.copyToClipboard(content, copyBtn));
      }

      const speakBtn = wrapper.querySelector('.speak-msg-btn');
      if (speakBtn && this.voice) {
        speakBtn.addEventListener('click', () => this.voice.speak(content));
      }

      const regenBtn = wrapper.querySelector('.regen-msg-btn');
      if (regenBtn) {
        regenBtn.addEventListener('click', () => this.regenerateLastResponse());
      }
    }

    if (window.lucide) window.lucide.createIcons();
    if (window.Prism) Prism.highlightAllUnder(wrapper);

    return wrapper;
  }

  showTypingIndicator() {
    const wrapper = document.createElement('div');
    wrapper.id = 'typing-indicator-wrapper';
    wrapper.className = 'message-wrapper assistant';
    wrapper.innerHTML = `
      <div class="message-avatar assistant">
        <i data-lucide="sparkles" style="width: 18px; height: 18px;"></i>
      </div>
      <div class="message-bubble" style="padding: 0.6rem 1rem;">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    this.messagesContainer.appendChild(wrapper);
    if (window.lucide) window.lucide.createIcons();
    this.scrollToBottom();
  }

  removeTypingIndicator() {
    const el = document.getElementById('typing-indicator-wrapper');
    if (el) el.remove();
  }

  async handleSendMessage() {
    const text = this.chatTextarea.value.trim();
    if (!text || this.isGenerating) return;

    this.lastUserMessage = text;
    this.chatTextarea.value = '';
    this.chatTextarea.style.height = 'auto';

    // Append user message
    this.appendMessageToDOM('user', text);
    this.scrollToBottom();

    // Start generation state
    this.isGenerating = true;
    this.sendBtn.style.display = 'none';
    if (this.stopBtn) this.stopBtn.style.display = 'inline-flex';

    this.updateOrbState('thinking', 'Dakshu is thinking...');
    this.showTypingIndicator();

    this.abortController = new AbortController();

    try {
      const headers = { 'Content-Type': 'application/json' };
      const token = DakshuApp.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          conversation_id: this.activeConversationId,
          message: text,
          module: this.activeModule,
          client_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata',
          client_location: this.userLocation || undefined,
          stream: true
        }),
        signal: this.abortController.signal
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      this.removeTypingIndicator();
      this.updateOrbState('responding', 'Dakshu is responding...');

      // Create assistant message wrapper
      const asstWrapper = document.createElement('div');
      asstWrapper.className = 'message-wrapper assistant';
      asstWrapper.innerHTML = `
        <div class="message-avatar assistant">
          <i data-lucide="sparkles" style="width: 18px; height: 18px;"></i>
        </div>
        <div class="message-bubble">
          <div class="message-text-content"></div>
          <div class="message-actions" style="display: none;">
            <button class="msg-btn copy-msg-btn"><i data-lucide="copy" style="width: 13px; height: 13px;"></i> Copy</button>
            <button class="msg-btn speak-msg-btn"><i data-lucide="volume-2" style="width: 13px; height: 13px;"></i> Speak</button>
            <button class="msg-btn regen-msg-btn"><i data-lucide="refresh-cw" style="width: 13px; height: 13px;"></i> Retry</button>
          </div>
        </div>
      `;
      this.messagesContainer.appendChild(asstWrapper);
      const textContentEl = asstWrapper.querySelector('.message-text-content');
      const actionsEl = asstWrapper.querySelector('.message-actions');

      if (window.lucide) window.lucide.createIcons();

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulatedText = '';
      let newConvId = this.activeConversationId;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const data = JSON.parse(raw);
              if (data.chunk) {
                accumulatedText += data.chunk;
                textContentEl.innerHTML = this.parseMarkdown(accumulatedText);
                this.scrollToBottom();
              }
              if (data.conversation_id) {
                newConvId = data.conversation_id;
              }
              if (data.done) {
                break;
              }
            } catch (e) {}
          }
        }
      }

      // Finish streaming
      actionsEl.style.display = 'flex';
      const copyBtn = asstWrapper.querySelector('.copy-msg-btn');
      const speakBtn = asstWrapper.querySelector('.speak-msg-btn');
      const regenBtn = asstWrapper.querySelector('.regen-msg-btn');

      if (copyBtn) copyBtn.addEventListener('click', () => this.copyToClipboard(accumulatedText, copyBtn));
      if (speakBtn && this.voice) speakBtn.addEventListener('click', () => this.voice.speak(accumulatedText));
      if (regenBtn) regenBtn.addEventListener('click', () => this.regenerateLastResponse());

      if (window.Prism) Prism.highlightAllUnder(asstWrapper);

      // Auto-speak if module is voice
      if (this.activeModule === 'voice' && this.voice) {
        this.voice.speak(accumulatedText);
      }

      // Refresh conversations sidebar if this was a new conversation
      if (!this.activeConversationId && newConvId) {
        this.activeConversationId = newConvId;
        await this.loadConversationsList();
      }
    } catch (e) {
      this.removeTypingIndicator();
      if (e.name === 'AbortError') {
        DakshuApp.showToast("Response generation stopped.", "info");
      } else {
        console.error("Chat streaming error:", e);
        this.appendMessageToDOM('assistant', "I apologize, but I encountered an issue connecting to the AI inference service. Please verify your connection or settings.");
      }
    } finally {
      this.isGenerating = false;
      this.sendBtn.style.display = 'inline-flex';
      if (this.stopBtn) this.stopBtn.style.display = 'none';
      this.updateOrbState('idle', 'Online • Ready');
      this.scrollToBottom();
    }
  }

  stopGeneration() {
    if (this.abortController) {
      this.abortController.abort();
    }
  }

  regenerateLastResponse() {
    if (this.lastUserMessage) {
      this.chatTextarea.value = this.lastUserMessage;
      this.handleSendMessage();
    }
  }

  copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
      const originalText = btn.innerHTML;
      btn.innerHTML = `<i data-lucide="check" style="width: 13px; height: 13px; color: var(--neon-emerald);"></i> Copied!`;
      if (window.lucide) window.lucide.createIcons();
      setTimeout(() => {
        btn.innerHTML = originalText;
        if (window.lucide) window.lucide.createIcons();
      }, 2000);
    });
  }

  parseMarkdown(text) {
    if (window.marked) {
      return marked.parse(text);
    }
    // Fallback safe formatting
    return this.escapeHtml(text)
      .replace(/\n\n/g, '<p></p>')
      .replace(/\n/g, '<br>');
  }

  escapeHtml(str) {
    const div = document.createElement('div');
    div.innerText = str;
    return div.innerHTML;
  }

  scrollToBottom() {
    if (this.messagesContainer) {
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
  }
}

// Auto instantiate on chat.html
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('chat-app-root')) {
    window.dakshuChat = new DakshuChatController();
  }
});

