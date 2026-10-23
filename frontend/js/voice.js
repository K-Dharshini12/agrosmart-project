// Voice Assistant Engine with Native Tamil Audio Streaming, Speed Control & Stop/Restart Controls

let currentVoiceLang = 'ta'; // 'ta' or 'en'
let synth = window.speechSynthesis;
let currentPlayingAudio = null;
let lastSpokenText = "";
let isRecording = false;
let callTimerInterval = null;
let callSeconds = 0;
let isCallMicMuted = false;
let isCallSpeakerOn = true;
let isCallListening = false;
let callRecognition = null;
let chatRecognition = null;

const VOICE_KNOWLEDGE = {
  ta: {
    callWelcome: "வணக்கம் உழவரே, உங்கள் தோட்டத்து பயிருக்கு என்ன உதவி வேண்டும்?",
    greeting: "வணக்கம் உழவரே, நான் உங்களின் உழவன் ஏஐ உதவியாளர். மண் ஈரப்பதம், மழை நிலவரம், உரம், பூச்சி மேலாண்மை அல்லது தக்காளி மண்டி விலை பற்றி கேளுங்கள்.",
    soilMoisture: "உங்கள் தோட்டத்தின் மண் ஈரப்பதம் தற்போது 78 சதவீதம் ஆக உள்ளது. இது தக்காளி செடிகளுக்கு மிகவும் உகந்த அளவு. இப்போது தண்ணீர் பாய்ச்ச தேவையில்லை.",
    weather: "நாளை உங்கள் பகுதியில் மழை பெய்ய வாய்ப்புள்ளது. வேர் அழுகல் மற்றும் நீர் தேங்குவதை தடுக்க நீர்ப்பாசனத்தை 50 சதவீதம் குறைத்துக் கொள்ளவும்.",
    pests: "தக்காளி இலைகளில் அசுவினி மற்றும் சாறு உறிஞ்சும் பூச்சிகள் தென்படுகின்றன. ஒரு லிட்டர் தண்ணீருக்கு 5 மில்லி வேப்பெண்ணெய் கலந்து அதிகாலை அல்லது மாலை வேளையில் தெளிக்கவும்.",
    harvest: "பழங்களின் நிற மாற்றத்தின்படி இன்னும் ஐந்து முதல் ஏழு நாட்களில் தக்காளி அறுவடைக்கு முழுமையாக தயாராகிவிடும்.",
    price: "இன்றைய மண்டி நிலவரப்படி தக்காளி கிலோவுக்கு 85 ரூபாய் வரை நல்ல விலைக்கு போகிறது. நல்ல கிராக்கி இருப்பதால் அறுவடை செய்ய உகந்த நேரம்.",
    fertilizer: "பூ மற்றும் காய் பிடிக்கும் பருவத்தில் பொட்டாசியம் மற்றும் பாஸ்பரஸ் தேவை அதிகம். 19 19 19 அல்லது 0 52 34 நீரில் கரையும் உரத்தை சொட்டுநீர் மூலம் கொடுக்கலாம்."
  },
  en: {
    callWelcome: "Vanakkam farmer! Tell me, what advice do you need for your crops today?",
    greeting: "Vanakkam! I'm your AgroSmart farm assistant. Ask me anything about soil moisture, weather, pests, tomato prices, or fertilizers in Tamil, Thanglish, or English!",
    soilMoisture: "Your live soil moisture is at 78%, which is optimal for tomato crops. Drip irrigation does not need to be triggered right now.",
    weather: "Tomorrow's forecast predicts rain in your region. It is recommended to reduce irrigation by 50% to prevent root rot and waterlogging.",
    pests: "Early aphid symptoms detected on lower tomato foliage. Spray 5ml neem oil mixed with 1ml liquid soap per liter of water early morning or late evening.",
    harvest: "Based on current color-break staging and vegetative growth index, your tomatoes will reach peak harvest readiness in 5 to 7 days.",
    price: "Current APMC Mandi tomato price is 85 rupees per kg with strong wholesale demand. High market advantage for immediate harvest planning.",
    fertilizer: "For the flowering to fruiting stage, apply NPK 13:0:45 or 0:52:34 along with Micronutrient mix via fertigation for high fruit setting."
  }
};

/**
 * Clean text thoroughly for natural speech synthesis
 * Strips all markdown symbols, asterisks, hashtags, dashes, brackets, colons, emojis
 */
function cleanSpeechText(raw) {
  if (!raw) return "";
  let clean = raw
    // Remove markdown code blocks & links
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    // Remove symbols: * # _ ~ ` > | ( ) [ ] { }
    .replace(/[*#_~`>|\(\)\[\]\{\}]/g, " ")
    // Remove bullet hyphens, bullets, and numbered prefixes like "1.", "2."
    .replace(/^\s*[-•*]\s+/gm, " ")
    .replace(/\s*[-–—]\s*/g, " ")
    .replace(/\b\d+\.\s*/g, " ")
    // Replace colons and semicolons with natural breath pauses (comma)
    .replace(/[:;]/g, ", ")
    // Remove emojis
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F018}-\u{1F270}\u{2388}\u{200D}]/gu, " ")
    // Normalize spaces
    .replace(/\s+/g, " ")
    .trim();

  // Limit to first 2-3 sentences for snappy, practical speech
  const sentences = clean.split(/(?<=[.?!।])\s+/);
  if (sentences.length > 3) {
    clean = sentences.slice(0, 3).join(" ");
  }
  return clean.substring(0, 240).trim();
}

/**
 * Stop any currently playing audio or speech synthesis
 */
function stopSpeech() {
  if (currentPlayingAudio) {
    try {
      currentPlayingAudio.pause();
      currentPlayingAudio.currentTime = 0;
    } catch (e) {}
    currentPlayingAudio = null;
  }

  if ('speechSynthesis' in window) {
    try {
      synth.cancel();
    } catch (e) {}
  }

  // Update UI speaking badges
  updateSpeakingStatusUI(false);
}

/**
 * Main Text-To-Speech player:
 * 1. Uses backend streaming native Tamil / English audio (/api/ai/tts)
 * 2. Speeds up slightly (rate = 1.08) for energetic, natural delivery
 * 3. Gracefully falls back to browser SpeechSynthesis if needed
 */
function speakText(text, lang = currentVoiceLang, onEndCallback = null) {
  stopSpeech();

  const clean = cleanSpeechText(text);
  if (!clean) {
    if (typeof onEndCallback === 'function') onEndCallback();
    return;
  }

  lastSpokenText = clean;
  updateSpeakingStatusUI(true, clean);

  const targetLang = (lang === 'ta' || lang === 'tamil' || lang === 'thanglish') ? 'ta' : 'en';

  // Strategy A: Native Tamil MP3 Audio Stream from backend endpoint
  const apiHost = window.AGRO_API_HOST || "";
  const audioUrl = `${apiHost}/api/ai/tts?text=${encodeURIComponent(clean)}&lang=${targetLang}`;
  const audio = new Audio(audioUrl);
  // User requested: "let the voice be a very little faster"
  audio.playbackRate = 1.08;
  currentPlayingAudio = audio;

  let audioPlaybackFailed = false;

  audio.onended = () => {
    currentPlayingAudio = null;
    updateSpeakingStatusUI(false);
    if (typeof onEndCallback === 'function') onEndCallback();
  };

  audio.onerror = (e) => {
    audioPlaybackFailed = true;
    console.warn("Native TTS audio failed, trying browser SpeechSynthesis fallback...", e);
    currentPlayingAudio = null;
    speakWithWebSpeechFallback(clean, targetLang, onEndCallback);
  };

  const playPromise = audio.play();
  if (playPromise !== undefined) {
    playPromise.catch(err => {
      if (!audioPlaybackFailed) {
        speakWithWebSpeechFallback(clean, targetLang, onEndCallback);
      }
    });
  }
}

/**
 * Browser SpeechSynthesis Fallback
 */
function speakWithWebSpeechFallback(cleanText, lang, onEndCallback) {
  if (!('speechSynthesis' in window)) {
    updateSpeakingStatusUI(false);
    if (typeof onEndCallback === 'function') onEndCallback();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  const voices = synth.getVoices();

  if (lang === 'ta') {
    const tamilVoice = voices.find(v => v.lang.toLowerCase().startsWith('ta') || v.name.toLowerCase().includes('tamil') || v.name.includes('Valluvar'));
    if (tamilVoice) utterance.voice = tamilVoice;
    utterance.lang = 'ta-IN';
  } else {
    const enVoice = voices.find(v => v.lang.toLowerCase().startsWith('en'));
    if (enVoice) utterance.voice = enVoice;
    utterance.lang = 'en-IN';
  }

  // Slightly faster speech rate (1.08)
  utterance.rate = 1.08;
  utterance.pitch = 1.0;

  utterance.onend = () => {
    updateSpeakingStatusUI(false);
    if (typeof onEndCallback === 'function') onEndCallback();
  };
  utterance.onerror = () => {
    updateSpeakingStatusUI(false);
    if (typeof onEndCallback === 'function') onEndCallback();
  };

  synth.speak(utterance);
}

/**
 * Re-read the last spoken response aloud
 */
function readAloudLast() {
  if (lastSpokenText) {
    speakText(lastSpokenText, currentVoiceLang);
  } else {
    const defaultGreeting = VOICE_KNOWLEDGE[currentVoiceLang]?.greeting || VOICE_KNOWLEDGE['ta'].greeting;
    speakText(defaultGreeting, currentVoiceLang);
  }
}

function updateSpeakingStatusUI(isPlaying, text = "") {
  const globalStopBtn = document.getElementById('global-speech-stop-btn');
  const globalWaveIndicator = document.getElementById('global-speech-indicator');

  if (globalStopBtn) {
    if (isPlaying) {
      globalStopBtn.classList.remove('hidden');
    } else {
      globalStopBtn.classList.add('hidden');
    }
  }

  if (globalWaveIndicator) {
    if (isPlaying) {
      globalWaveIndicator.classList.remove('hidden');
    } else {
      globalWaveIndicator.classList.add('hidden');
    }
  }
}

function setLanguage(lang) {
  currentVoiceLang = lang;
  const greeting = VOICE_KNOWLEDGE[lang]?.greeting || VOICE_KNOWLEDGE['ta'].greeting;
  const greetingEl = document.getElementById('initial-ai-greeting');
  if (greetingEl) greetingEl.innerText = greeting;
}

// Inline Chat Speech Recognition (Tamil & English)
function toggleVoiceRecording() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
    return;
  }

  const btn = document.getElementById('voice-record-btn');
  if (isRecording) {
    if (chatRecognition) chatRecognition.stop();
    isRecording = false;
    btn.classList.remove('bg-red-500', 'text-white', 'farm-pulse');
    btn.classList.add('bg-farm-100', 'text-farm-700');
    return;
  }

  chatRecognition = new SpeechRecognition();
  chatRecognition.lang = currentVoiceLang === 'ta' ? 'ta-IN' : 'en-IN';
  chatRecognition.interimResults = false;

  chatRecognition.onstart = () => {
    isRecording = true;
    btn.classList.add('bg-red-500', 'text-white', 'farm-pulse');
    btn.classList.remove('bg-farm-100', 'text-farm-700');
  };

  chatRecognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('chat-input').value = transcript;
    sendChatMessage();
  };

  chatRecognition.onerror = () => {
    isRecording = false;
    btn.classList.remove('bg-red-500', 'text-white', 'farm-pulse');
    btn.classList.add('bg-farm-100', 'text-farm-700');
  };

  chatRecognition.onend = () => {
    isRecording = false;
    btn.classList.remove('bg-red-500', 'text-white', 'farm-pulse');
    btn.classList.add('bg-farm-100', 'text-farm-700');
  };

  chatRecognition.start();
}

// -------------------------------------------------------------
// Interactive Voice Call Simulator with Full Stop & Restart
// -------------------------------------------------------------
function startVoiceCallModal() {
  const modal = document.getElementById('voice-call-modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');

  callSeconds = 0;
  isCallMicMuted = false;
  isCallSpeakerOn = true;

  const langName = currentVoiceLang === 'ta' ? 'தமிழ் / Thanglish' : 'English';
  document.getElementById('call-lang-label').innerText = `Speaking in ${langName}`;
  
  const welcome = VOICE_KNOWLEDGE[currentVoiceLang]?.callWelcome || VOICE_KNOWLEDGE['ta'].callWelcome;
  document.getElementById('call-transcript-quote').innerText = `"${welcome}"`;
  document.getElementById('call-status-line').innerText = "🔊 உழவன் தோழன் பேசுகிறது... (Speaking...)";

  clearInterval(callTimerInterval);
  callTimerInterval = setInterval(() => {
    callSeconds++;
    const mins = String(Math.floor(callSeconds / 60)).padStart(2, '0');
    const secs = String(callSeconds % 60).padStart(2, '0');
    document.getElementById('call-timer').innerText = `${mins}:${secs}`;
  }, 1000);

  // Speak welcome aloud, then listen to farmer
  speakText(welcome, currentVoiceLang, () => {
    if (!isCallMicMuted && modal.classList.contains('flex')) {
      startCallListening();
    }
  });

  lucide.createIcons();
}

function startCallListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    document.getElementById('call-status-line').innerText = "🎤 Speech recognition unavailable on this browser";
    return;
  }

  if (isCallMicMuted) return;

  try {
    if (callRecognition) {
      callRecognition.abort();
    }
    callRecognition = new SpeechRecognition();
    callRecognition.lang = currentVoiceLang === 'ta' ? 'ta-IN' : 'en-IN';
    callRecognition.interimResults = false;

    callRecognition.onstart = () => {
      isCallListening = true;
      document.getElementById('call-status-line').innerText = "🔴 நீங்கள் பேசுவதைக் கேட்கிறது... (Listening now...)";
      const micBtn = document.getElementById('btn-call-mic');
      if (micBtn) micBtn.classList.add('farm-pulse');
    };

    callRecognition.onresult = async (event) => {
      const userText = event.results[0][0].transcript;
      if (!userText || !userText.trim()) return;

      document.getElementById('call-transcript-quote').innerText = `🗣️ "${userText}"`;
      document.getElementById('call-status-line').innerText = "🤖 உழவன் தோழன் யோசிக்கிறது... (Analyzing...)";

      // Call AI Backend with location context
      const locationContext = window.getCurrentPlaceContext ? window.getCurrentPlaceContext() : null;
      let reply = null;
      try {
        const res = await AgroAPI.chatWithAI(userText, currentVoiceLang, locationContext);
        if (res) {
          reply = res.speech_text || res.reply;
        }
      } catch (err) {
        console.warn("Call chat API error:", err);
      }

      if (!reply) {
        const k = VOICE_KNOWLEDGE[currentVoiceLang] || VOICE_KNOWLEDGE['ta'];
        reply = k.soilMoisture;
      }

      const cleanReply = cleanSpeechText(reply);
      document.getElementById('call-transcript-quote').innerText = `🤖 "${cleanReply}"`;
      document.getElementById('call-status-line').innerText = "🔊 உழவன் தோழன் பதிலளிக்கிறது... (Speaking...)";

      // Speak reply out loud at 1.08x speed
      speakText(cleanReply, currentVoiceLang, () => {
        const modal = document.getElementById('voice-call-modal');
        if (modal && modal.classList.contains('flex') && !isCallMicMuted) {
          setTimeout(startCallListening, 700);
        }
      });
    };

    callRecognition.onerror = (e) => {
      isCallListening = false;
      document.getElementById('call-status-line').innerText = "🎤 மைக்கை தட்டி மீண்டும் பேசவும் (Tap mic to speak)";
    };

    callRecognition.onend = () => {
      isCallListening = false;
      const micBtn = document.getElementById('btn-call-mic');
      if (micBtn) micBtn.classList.remove('farm-pulse');
    };

    callRecognition.start();
  } catch (err) {
    console.warn("Recognition start failed:", err);
  }
}

function endVoiceCallModal() {
  stopSpeech();
  const modal = document.getElementById('voice-call-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  clearInterval(callTimerInterval);
  if (callRecognition) {
    callRecognition.abort();
    callRecognition = null;
  }
}

function toggleCallMic() {
  isCallMicMuted = !isCallMicMuted;
  const btn = document.getElementById('btn-call-mic');
  if (isCallMicMuted) {
    if (callRecognition) callRecognition.abort();
    btn.classList.add('bg-red-100', 'text-red-600');
    document.getElementById('call-status-line').innerText = "🔇 மைக் அணைக்கப்பட்டது (Muted)";
  } else {
    btn.classList.remove('bg-red-100', 'text-red-600');
    document.getElementById('call-status-line').innerText = "🎤 பேசத் தயார்... (Listening...)";
    startCallListening();
  }
}

function toggleCallSpeaker() {
  isCallSpeakerOn = !isCallSpeakerOn;
  const btn = document.getElementById('btn-call-speaker');
  if (!isCallSpeakerOn) {
    btn.classList.add('bg-stone-200');
    stopSpeech();
  } else {
    btn.classList.remove('bg-stone-200');
    readAloudLast();
  }
}
