/**
 * DAKSHU AI - Voice Companion Engine
 * Speech Recognition (STT) and Speech Synthesis (TTS)
 */

class DakshuVoiceEngine {
  constructor(orbVisualizer = null) {
    this.orb = orbVisualizer;
    this.recognition = null;
    this.synthesis = window.speechSynthesis || null;
    this.isRecording = false;
    this.isVoiceSpeaking = false;
    this.voiceEnabled = true;

    // Callbacks
    this.onResult = null;
    this.onStateChange = null;

    this.initSpeechRecognition();
  }

  setOrb(orbVisualizer) {
    this.orb = orbVisualizer;
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("Dakshu AI: Web Speech Recognition API is not supported in this browser.");
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US'; // Or 'ta-IN' if preferred

      this.recognition.onstart = () => {
        this.isRecording = true;
        if (this.orb) {
          this.orb.setState('listening');
          this.orb.setAudioLevel(0.4);
        }
        if (this.onStateChange) this.onStateChange('listening');
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }

        // Simulate reactive audio surge
        if (this.orb) {
          this.orb.setAudioLevel(0.8);
          setTimeout(() => this.orb.setAudioLevel(0.3), 300);
        }

        if (this.onResult) {
          this.onResult(transcript, event.results[event.results.length - 1].isFinal);
        }
      };

      this.recognition.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        this.stopListening();
        if (this.onStateChange) this.onStateChange('error', event.error);
      };

      this.recognition.onend = () => {
        this.isRecording = false;
        if (this.orb) {
          this.orb.setState('idle');
          this.orb.setAudioLevel(0);
        }
        if (this.onStateChange) this.onStateChange('idle');
      };
    } catch (e) {
      console.error("Failed to initialize speech recognition:", e);
    }
  }

  isSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  startListening(onResult, onStateChange) {
    if (!this.recognition) {
      if (onStateChange) onStateChange('unsupported');
      return false;
    }

    if (this.isVoiceSpeaking) {
      this.stopSpeaking();
    }

    this.onResult = onResult;
    this.onStateChange = onStateChange;

    try {
      this.recognition.start();
      return true;
    } catch (e) {
      console.warn("Recognition already active or failed to start:", e);
      return false;
    }
  }

  stopListening() {
    if (this.recognition && this.isRecording) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
    this.isRecording = false;
    if (this.orb) {
      this.orb.setState('idle');
      this.orb.setAudioLevel(0);
    }
  }

  toggleListening(onResult, onStateChange) {
    if (this.isRecording) {
      this.stopListening();
      return false;
    } else {
      return this.startListening(onResult, onStateChange);
    }
  }

  speak(text, onStart, onEnd) {
    if (!this.synthesis || !this.voiceEnabled || !text) return;

    // Strip markdown symbols and code blocks for clean TTS reading
    const cleanText = text
      .replace(/```[\s\S]*?```/g, 'Code snippet provided in chat.')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/[#*_~>]/g, '')
      .trim();

    if (!cleanText) return;

    // Cancel any current utterance
    this.synthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.05; // Slightly warmer/friendly pitch

    // Choose preferred voice if available
    const voices = this.synthesis.getVoices();
    const preferredVoice = voices.find(v => (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('India')) && v.lang.startsWith('en'));
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => {
      this.isVoiceSpeaking = true;
      if (this.orb) {
        this.orb.setState('responding');
        this.orb.setAudioLevel(0.6);
      }
      if (onStart) onStart();
    };

    utterance.onend = () => {
      this.isVoiceSpeaking = false;
      if (this.orb) {
        this.orb.setState('idle');
        this.orb.setAudioLevel(0);
      }
      if (onEnd) onEnd();
    };

    utterance.onerror = () => {
      this.isVoiceSpeaking = false;
      if (this.orb) {
        this.orb.setState('idle');
        this.orb.setAudioLevel(0);
      }
      if (onEnd) onEnd();
    };

    this.synthesis.speak(utterance);
  }

  stopSpeaking() {
    if (this.synthesis) {
      this.synthesis.cancel();
    }
    this.isVoiceSpeaking = false;
    if (this.orb) {
      this.orb.setState('idle');
      this.orb.setAudioLevel(0);
    }
  }
}

window.DakshuVoice = DakshuVoiceEngine;

