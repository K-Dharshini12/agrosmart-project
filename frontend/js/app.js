// AgroSmart / Ulavan Connect AI - Main Application Controller

let currentSiteLanguage = localStorage.getItem('agro_site_lang') || 'ta';
let localMediaStream = null;
let staticNoiseAnimationId = null;
let searchDebounceTimer = null;

// Default Selected Agricultural Location
let currentPlace = {
  name: "Coimbatore",
  lat: 11.0055,
  lon: 76.9661,
  name_ta: "கோயம்புத்தூர்"
};

try {
  const savedPlace = localStorage.getItem('agro_selected_place');
  if (savedPlace) {
    currentPlace = JSON.parse(savedPlace);
  }
} catch (e) {}

let currentWeatherContext = {
  weather_condition: "Sunny & Clear",
  air_temperature: 28,
  humidity: 65,
  rain_probability: "10%"
};

// Global accessor for Voice and AI modules
window.getCurrentPlaceContext = function() {
  return {
    location: `${currentPlace.name} (${currentPlace.name_ta || currentPlace.name})`,
    weather_condition: currentWeatherContext.weather_condition,
    air_temperature: currentWeatherContext.air_temperature,
    humidity: currentWeatherContext.humidity,
    rain_probability: currentWeatherContext.rain_probability
  };
};

document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  startClock();
  initData();
  setupWebSocket();
  initTvStatic();
  applyLanguage(currentSiteLanguage);
  updatePlaceUI(currentPlace);
  loadPlaceWeather(currentPlace.name, currentPlace.lat, currentPlace.lon);
});

// ==========================================
// 1. Full Website Language Switching
// ==========================================
function changeSiteLanguage(lang) {
  currentSiteLanguage = lang;
  window.currentSiteLanguage = lang;
  localStorage.setItem('agro_site_lang', lang);
  applyLanguage(lang);
}

function toggleLanguageGlobal() {
  const current = currentSiteLanguage || 'ta';
  const nextLang = (current === 'ta' || current === 'tamil') ? 'en' : 'ta';
  changeSiteLanguage(nextLang);
  if (typeof showToast === 'function') {
    showToast(nextLang === 'ta' ? 'தமிழ் மொழி தேர்ந்தெடுக்கப்பட்டது (Tamil View)' : 'Switched to English View');
  }
}
window.toggleLanguageGlobal = toggleLanguageGlobal;

function applyLanguage(lang) {
  const dict = TRANSLATIONS[lang] || TRANSLATIONS['ta'];

  // Update text nodes
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.innerText = dict[key];
    }
  });

  // Update placeholder nodes
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    if (dict[key]) {
      el.placeholder = dict[key];
    }
  });

  // Update language switcher pill buttons
  const taEl = document.getElementById('langTA');
  const enEl = document.getElementById('langEN');
  if (lang === 'ta') {
    if (taEl) {
      taEl.className = 'text-primary font-bold';
    }
    if (enEl) {
      enEl.className = 'text-on-surface-variant font-medium';
    }
  } else {
    if (enEl) {
      enEl.className = 'text-primary font-bold';
    }
    if (taEl) {
      taEl.className = 'text-on-surface-variant font-medium';
    }
  }

  // Sync voice engine
  if (typeof setLanguage === 'function') {
    setLanguage(lang);
  }

  document.documentElement.lang = lang;
  updatePlaceUI(currentPlace);
  if (window.lucide && typeof lucide.createIcons === 'function') {
    lucide.createIcons();
  }
}

// ==========================================
// 2. Tab Navigation
// ==========================================
function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.getElementById(`tab-${tabName}`).classList.remove('hidden');

  const tabs = ['dashboard', 'controls', 'marketplace'];
  tabs.forEach(t => {
    const btn = document.getElementById(`nav-${t}`);
    if (t === tabName) {
      btn.className = "nav-btn flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all bg-farm-800 text-white shadow-farm";
    } else {
      btn.className = "nav-btn flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all text-stone-600 hover:bg-stone-100";
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Live Clock
function startClock() {
  const clockEl = document.getElementById('live-clock');
  const cctvTimeEl = document.getElementById('cctv-timestamp');
  setInterval(() => {
    const now = new Date();
    if (clockEl) clockEl.innerText = now.toLocaleTimeString();
    if (cctvTimeEl) cctvTimeEl.innerText = `LIVE ${now.toISOString().replace('T', ' ').substring(0, 19)}`;
  }, 1000);
}

// Initial Data Loading
async function initData() {
  const telemetry = await AgroAPI.getLatestTelemetry();
  updateTelemetryUI(telemetry);
}

function setupWebSocket() {
  AgroAPI.initWebSocket((data) => {
    updateTelemetryUI(data);
  });
}

function updateTelemetryUI(data) {
  if (!data) return;
  if (data.soil_moisture !== undefined) {
    document.getElementById('sensor-moisture').innerText = Math.round(data.soil_moisture);
    document.getElementById('header-moisture').innerText = `${Math.round(data.soil_moisture)}%`;
  }
  if (data.soil_temperature !== undefined) {
    document.getElementById('sensor-temp').innerText = Math.round(data.soil_temperature);
  }
  if (data.soil_ph !== undefined) {
    document.getElementById('sensor-ph').innerText = data.soil_ph.toFixed(1);
  }
  if (data.water_tank_level !== undefined) {
    document.getElementById('sensor-tank').innerText = Math.round(data.water_tank_level);
  }
}

// ==========================================
// 3. Location Selector & Real Place Weather
// ==========================================
function openLocationModal() {
  const modal = document.getElementById('location-modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  lucide.createIcons();
}

function closeLocationModal() {
  const modal = document.getElementById('location-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

function updatePlaceUI(place) {
  const heroPlaceEl = document.getElementById('hero-selected-place');
  if (heroPlaceEl) {
    const label = currentSiteLanguage === 'en' 
      ? place.name 
      : (place.name_ta ? `${place.name} (${place.name_ta})` : place.name);
    heroPlaceEl.innerText = label;
  }
  const sectorTitle = document.getElementById('dashboard-sector-title');
  if (sectorTitle) {
    sectorTitle.innerText = `${place.name} Smart Farm Sector 4B`;
  }
  const sectorSub = document.getElementById('dashboard-sector-subtitle');
  if (sectorSub) {
    sectorSub.innerText = place.name_ta 
      ? `${place.name_ta} வயல் பகுதி 4B • Live Telemetry Active`
      : `${place.name} Field Sector 4B • Live Telemetry Active`;
  }
}

async function selectPlace(name, lat, lon, name_ta = "") {
  currentPlace = { name, lat, lon, name_ta };
  localStorage.setItem('agro_selected_place', JSON.stringify(currentPlace));
  updatePlaceUI(currentPlace);
  closeLocationModal();

  // Load real meteorological data for this place
  await loadPlaceWeather(name, lat, lon);
}

async function loadPlaceWeather(name, lat, lon) {
  const weatherData = await AgroAPI.getLivePlaceWeather(name, lat, lon);
  if (!weatherData) return;

  const current = weatherData.current;
  const forecast = weatherData.forecast;

  // Save in global state for AI prompts
  currentWeatherContext = {
    weather_condition: currentSiteLanguage === 'en' ? current.condition_en : current.condition_ta,
    air_temperature: current.temperature,
    humidity: current.humidity,
    rain_probability: forecast?.tomorrow?.rain_prob ? `${forecast.tomorrow.rain_prob}%` : "30%"
  };

  // Update Hero Temperature Pill & Stitch Weather Bar
  const heroTempEl = document.getElementById('hero-live-temp');
  if (heroTempEl) {
    heroTempEl.innerText = `${Math.round(current.temperature)}°C`;
  }
  const weatherTempEl = document.getElementById('weather-temp-display');
  if (weatherTempEl) weatherTempEl.innerText = `${Math.round(current.temperature)}°C`;
  const weatherCondEl = document.getElementById('weather-cond-display');
  if (weatherCondEl) weatherCondEl.innerText = currentSiteLanguage === 'en' ? current.condition_en : current.condition_ta;
  const weatherWindEl = document.getElementById('weather-wind-display');
  if (weatherWindEl && current.wind_speed !== undefined) weatherWindEl.innerText = Math.round(current.wind_speed);

  // Update Sensor Cards on Dashboard
  // 1. Weather Card
  const weatherCard = document.querySelector('[data-i18n="sensor.weather.title"]')?.closest('.sensor-card');
  if (weatherCard) {
    const tempVal = weatherCard.querySelector('.text-3xl');
    if (tempVal) tempVal.innerText = Math.round(current.temperature);
    
    const condDesc = weatherCard.querySelector('[data-i18n="sensor.weather.change"]');
    if (condDesc) {
      condDesc.innerText = `${current.icon} ${currentSiteLanguage === 'en' ? current.condition_en : current.condition_ta}`;
    }

    const rainDesc = weatherCard.querySelector('[data-i18n="sensor.weather.desc"]');
    if (rainDesc && forecast?.tomorrow) {
      const prob = forecast.tomorrow.rain_prob;
      rainDesc.innerText = currentSiteLanguage === 'en' 
        ? `Rain chance tomorrow: ${prob}% • Humidity ${current.humidity}%` 
        : `நாளை மழை பெய்ய வாய்ப்பு: ${prob}% • ஈரப்பதம் ${current.humidity}%`;
    }
  }

  // 2. Real Soil Moisture Card
  const moistureVal = document.getElementById('sensor-moisture');
  if (moistureVal && current.soil_moisture_pct) {
    moistureVal.innerText = current.soil_moisture_pct;
    document.getElementById('header-moisture').innerText = `${current.soil_moisture_pct}%`;
  }

  // 3. Root Soil Temperature Card
  const tempSensorVal = document.getElementById('sensor-temp');
  if (tempSensorVal && current.soil_temperature) {
    tempSensorVal.innerText = Math.round(current.soil_temperature);
  }

  // 4. Update Forecast Slots in Controls Tab
  if (forecast) {
    const updateSlot = (idPrefix, slotData) => {
      const el = document.getElementById(idPrefix);
      if (el && slotData) {
        el.innerText = `${slotData.icon || '🌤️'} ${slotData.temp}°C (${slotData.rain_prob}% rain)`;
      }
    };
    updateSlot('controls-w-now', forecast.now);
    updateSlot('controls-w-2pm', forecast.after_2h);
    updateSlot('controls-w-6pm', forecast.evening);
    updateSlot('controls-w-tmrw', forecast.tomorrow);
  }
}

function handleLocationSearch(query) {
  clearTimeout(searchDebounceTimer);
  const container = document.getElementById('location-search-results');
  if (!query || query.trim().length < 2) {
    container.classList.add('hidden');
    container.innerHTML = "";
    return;
  }

  searchDebounceTimer = setTimeout(async () => {
    container.innerHTML = `<div class="p-3 text-stone-400 italic">தேடுகிறது... (Searching places)</div>`;
    container.classList.remove('hidden');

    const results = await AgroAPI.searchPlaces(query.trim());
    if (!results || results.length === 0) {
      container.innerHTML = `<div class="p-3 text-stone-500">இடங்கள் கிடைக்கவில்லை. வேறு ஊர் பெயரை முயற்சிக்கவும்.</div>`;
      return;
    }

    container.innerHTML = "";
    results.forEach(r => {
      const item = document.createElement('div');
      item.className = "p-2.5 hover:bg-farm-50 cursor-pointer flex items-center justify-between text-stone-800 transition-colors";
      item.innerHTML = `
        <div class="flex items-center space-x-2">
          <span>📍</span>
          <div>
            <span class="font-semibold">${r.name}</span>
            <span class="text-[10px] text-stone-500 block">${r.admin1 || ''}, ${r.country || ''}</span>
          </div>
        </div>
        <span class="text-[10px] text-farm-700 bg-farm-100 px-2 py-0.5 rounded font-mono">Select</span>
      `;
      item.onclick = () => selectPlace(r.name, r.latitude, r.longitude, r.name);
      container.appendChild(item);
    });
  }, 350);
}

// ==========================================
// 4. CCTV TV Static & Real Connection
// ==========================================
function initTvStatic() {
  const canvas = document.getElementById('cctv-static-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width = 320;
  canvas.height = 180;

  function renderNoise() {
    const w = canvas.width;
    const h = canvas.height;
    const imgData = ctx.createImageData(w, h);
    const buffer32 = new Uint32Array(imgData.data.buffer);
    const len = buffer32.length;

    // Fast static noise loop
    for (let i = 0; i < len; i++) {
      // 50% random grey/white pixels
      if (Math.random() < 0.5) {
        const val = Math.floor(Math.random() * 180) + 40;
        buffer32[i] = (255 << 24) | (val << 16) | (val << 8) | val;
      } else {
        buffer32[i] = (255 << 24) | (15 << 16) | (15 << 8) | 15;
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Subtle horizontal CRT scanlines
    ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
    for (let y = 0; y < h; y += 4) {
      ctx.fillRect(0, y, w, 1.5);
    }

    staticNoiseAnimationId = requestAnimationFrame(renderNoise);
  }

  renderNoise();
}

function openCctvConnectModal() {
  const modal = document.getElementById('cctv-modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  lucide.createIcons();
}

function closeCctvConnectModal() {
  const modal = document.getElementById('cctv-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

// Connect Method 1: Local Device Webcam / Phone Camera
async function connectLocalWebcam() {
  closeCctvConnectModal();

  try {
    localMediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: "environment"
      },
      audio: false
    });

    const videoEl = document.getElementById('cctv-video-stream');
    videoEl.srcObject = localMediaStream;
    videoEl.classList.remove('hidden');

    // Stop and hide TV static
    if (staticNoiseAnimationId) cancelAnimationFrame(staticNoiseAnimationId);
    document.getElementById('cctv-static-canvas').classList.add('hidden');
    document.getElementById('cctv-disconnected-overlay').classList.add('hidden');
    document.getElementById('cctv-live-hud').classList.remove('hidden');

    // Update status badge to Live
    const badge = document.getElementById('cctv-status-badge');
    badge.className = "text-xs bg-red-100 text-red-600 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider flex items-center space-x-1.5 border border-red-200";
    document.getElementById('cctv-status-dot').className = "w-2 h-2 rounded-full bg-red-600 farm-pulse";
    document.getElementById('cctv-status-text').innerText = currentSiteLanguage === 'en' ? "🔴 LIVE FEED • 30 FPS" : "🔴 நேரலை (LIVE) • 30 FPS";

    // Toggle Buttons
    document.getElementById('btn-open-cctv-modal').classList.add('hidden');
    document.getElementById('btn-disconnect-cctv').classList.remove('hidden');

    // Notify Backend
    AgroAPI.connectCctv({
      camera_name: "Local Device Webcam",
      stream_url: "local_webcam_stream",
      source_type: "webcam"
    });

    lucide.createIcons();
  } catch (err) {
    alert("Camera permission denied or camera unavailable: " + err.message);
  }
}

// Connect Method 2: IP Camera / RTSP Video Stream
async function connectStreamUrl() {
  const urlInput = document.getElementById('cctv-stream-url-input');
  const nameInput = document.getElementById('cctv-cam-name-input');
  const streamUrl = (urlInput.value || "").trim();
  const camName = (nameInput.value || "Farm IP Cam").trim();

  if (!streamUrl) {
    alert("Please enter a valid RTSP / HTTP video stream URL.");
    return;
  }

  closeCctvConnectModal();

  const videoEl = document.getElementById('cctv-video-stream');
  videoEl.srcObject = null;
  videoEl.src = streamUrl;
  videoEl.classList.remove('hidden');

  // Stop static noise
  if (staticNoiseAnimationId) cancelAnimationFrame(staticNoiseAnimationId);
  document.getElementById('cctv-static-canvas').classList.add('hidden');
  document.getElementById('cctv-disconnected-overlay').classList.add('hidden');
  document.getElementById('cctv-live-hud').classList.remove('hidden');

  // Update Camera Label
  document.getElementById('cctv-cam-label').innerText = `${camName} • 1080p`;

  // Status Badge
  const badge = document.getElementById('cctv-status-badge');
  badge.className = "text-xs bg-red-100 text-red-600 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider flex items-center space-x-1.5 border border-red-200";
  document.getElementById('cctv-status-dot').className = "w-2 h-2 rounded-full bg-red-600 farm-pulse";
  document.getElementById('cctv-status-text').innerText = "🔴 LIVE IP STREAM";

  document.getElementById('btn-open-cctv-modal').classList.add('hidden');
  document.getElementById('btn-disconnect-cctv').classList.remove('hidden');

  AgroAPI.connectCctv({
    camera_name: camName,
    stream_url: streamUrl,
    source_type: "ip_stream"
  });

  lucide.createIcons();
}

// Disconnect CCTV (Restore TV Static & No Signal Overlay)
function disconnectRealCctv() {
  // Stop webcam tracks if active
  if (localMediaStream) {
    localMediaStream.getTracks().forEach(track => track.stop());
    localMediaStream = null;
  }

  const videoEl = document.getElementById('cctv-video-stream');
  videoEl.pause();
  videoEl.srcObject = null;
  videoEl.removeAttribute('src');
  videoEl.classList.add('hidden');

  // Hide HUD, Show Static Noise & Disconnected OSD
  document.getElementById('cctv-live-hud').classList.add('hidden');
  document.getElementById('cctv-static-canvas').classList.remove('hidden');
  document.getElementById('cctv-disconnected-overlay').classList.remove('hidden');

  // Restart static noise loop
  initTvStatic();

  // Reset Status Badge
  const badge = document.getElementById('cctv-status-badge');
  badge.className = "text-xs bg-stone-100 text-stone-600 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider flex items-center space-x-1.5 border border-stone-200";
  document.getElementById('cctv-status-dot').className = "w-2 h-2 rounded-full bg-stone-400";
  document.getElementById('cctv-status-text').innerText = currentSiteLanguage === 'en' ? "⚫ NO SIGNAL • DISCONNECTED" : "⚫ சிக்னல் இல்லை (DISCONNECTED)";

  // Buttons
  document.getElementById('btn-open-cctv-modal').classList.remove('hidden');
  document.getElementById('btn-disconnect-cctv').classList.add('hidden');

  AgroAPI.disconnectCctv();
  lucide.createIcons();
}

// ==========================================
// 5. Chat UI with Direct & Relevant Answers
// ==========================================
async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = "";

  appendMessage("user", text);

  // Show thinking indicator
  const container = document.getElementById('chat-messages');
  const thinkingDiv = document.createElement('div');
  thinkingDiv.id = "thinking-bubble";
  thinkingDiv.className = "bg-farm-50 text-farm-800 p-3 rounded-lg border border-farm-100 max-w-[85%] text-xs italic flex items-center space-x-2";
  const thinkText = currentSiteLanguage === 'en' ? "AgroSmart AI is thinking..." : "உழவன் தோழன் யோசிக்கிறது... (Thinking)";
  thinkingDiv.innerHTML = `<span class="w-2 h-2 rounded-full bg-farm-600 farm-pulse"></span><span>${thinkText}</span>`;
  container.appendChild(thinkingDiv);
  container.scrollTop = container.scrollHeight;

  // Call API with Location Context
  let replyText = null;
  let engineName = currentSiteLanguage === 'en' ? "AgroSmart AI" : "உழவன் தோழன்";
  const placeContext = window.getCurrentPlaceContext();

  const apiRes = await AgroAPI.chatWithAI(text, currentSiteLanguage, placeContext);
  
  // Remove thinking indicator
  const thinkEl = document.getElementById('thinking-bubble');
  if (thinkEl) thinkEl.remove();

  let speechText = null;

  if (apiRes && apiRes.reply) {
    replyText = apiRes.reply;
    speechText = apiRes.speech_text || apiRes.reply;
    if (apiRes.engine) engineName += ` (${apiRes.engine})`;
  } else {
    // Client fallback NLP
    const lower = text.toLowerCase();
    const k = VOICE_KNOWLEDGE[currentSiteLanguage] || VOICE_KNOWLEDGE['ta'];
    if (lower.includes("soil") || lower.includes("moisture") || lower.includes("மண்") || lower.includes("thanni") || lower.includes("eeram") || lower.includes("paachalama")) {
      replyText = k.soilMoisture;
    } else if (lower.includes("weather") || lower.includes("rain") || lower.includes("வானிலை") || lower.includes("mazhai") || lower.includes("malai")) {
      replyText = k.weather;
    } else if (lower.includes("pest") || lower.includes("பூச்சி") || lower.includes("poochi") || lower.includes("marunthu") || lower.includes("spray")) {
      replyText = k.pests;
    } else if (lower.includes("harvest") || lower.includes("அறுவடை") || lower.includes("aruvadai") || lower.includes("arukalam") || lower.includes("parikka")) {
      replyText = k.harvest;
    } else if (lower.includes("price") || lower.includes("mandi") || lower.includes("விலை") || lower.includes("rate") || lower.includes("kasu")) {
      replyText = k.price;
    } else if (lower.includes("uram") || lower.includes("fertilizer") || lower.includes("urea") || lower.includes("potash")) {
      replyText = k.fertilizer;
    } else {
      replyText = k.greeting;
    }
    speechText = replyText;
  }

  appendMessage("ai", replyText, engineName, speechText);
  speakText(speechText || replyText, currentSiteLanguage);
}

function quickPrompt(topic) {
  const prompts = {
    soil: { ta: "Thanni paachalama bro? Mann eeram eppadi irukku?", en: "How is my soil moisture today?" },
    weather: { ta: "Nalaiki mazhai varuma? Paasanam eppadi pannanum?", en: "Will it rain tomorrow? How should I irrigate?" },
    pest: { ta: "Thakkali chediyila poochi thollai jaasthi ah irukku, enna spray pannalam?", en: "What organic spray should I use for tomato pests?" },
    harvest: { ta: "Thakkali eppo arukalam? Harvest ready ah?", en: "When can I harvest my tomatoes?" },
    price: { ta: "Thakkali rate enna ippo mandiyila? Nalla vilaikku pogutha?", en: "What is the current tomato mandi price?" },
    fertilizer: { ta: "Poo pidikkura time-la enna uram podanum?", en: "What fertilizer should I apply during flowering stage?" }
  };
  const text = prompts[topic][currentSiteLanguage] || prompts[topic].ta;
  document.getElementById('chat-input').value = text;
  sendChatMessage();
}

function appendMessage(sender, text, customSender = null, speechText = null) {
  const container = document.getElementById('chat-messages');
  const msgDiv = document.createElement('div');
  const isUser = sender === 'user';
  
  const userLabel = currentSiteLanguage === 'en' ? '👤 You (Farmer)' : '👤 You (உழவர்)';
  const senderTitle = isUser ? userLabel : (customSender || (currentSiteLanguage === 'en' ? '🤖 AgroSmart AI' : '🤖 உழவன் தோழன்'));

  msgDiv.className = isUser 
    ? "bg-stone-800 text-white p-3 rounded-lg ml-auto max-w-[85%]" 
    : "bg-farm-50 text-farm-950 p-3.5 rounded-lg border border-farm-200 max-w-[85%]";

  window.chatSpeechRegistry = window.chatSpeechRegistry || [];
  const speechIndex = window.chatSpeechRegistry.push(speechText || text) - 1;

  const aiVoiceActionButtons = !isUser ? `
    <div class="mt-2.5 pt-2 border-t border-farm-200/60 flex flex-wrap items-center gap-2">
      <button onclick="speakText(window.chatSpeechRegistry[${speechIndex}], currentSiteLanguage)" class="px-2.5 py-1 text-[11px] rounded bg-white hover:bg-farm-100 text-farm-800 border border-farm-200 font-semibold flex items-center space-x-1 shadow-2xs transition-all">
        <span>🔊</span>
        <span>மீண்டும் வாசி (Read Aloud)</span>
      </button>
      <button onclick="stopSpeech()" class="px-2.5 py-1 text-[11px] rounded bg-white hover:bg-red-50 text-red-600 border border-stone-200 font-semibold flex items-center space-x-1 shadow-2xs transition-all">
        <span>⏹️</span>
        <span>நிறுத்து (Stop)</span>
      </button>
    </div>
  ` : '';

  msgDiv.innerHTML = `
    <div class="flex items-center space-x-2 text-xs font-semibold ${isUser ? 'text-stone-300' : 'text-farm-800'} mb-1.5">
      <span>${senderTitle}</span>
      <span class="text-[10px] text-stone-400 font-normal">Just now</span>
    </div>
    <div class="text-sm leading-relaxed whitespace-pre-wrap">${text}</div>
    ${aiVoiceActionButtons}
  `;
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

// Valve Toggles
async function toggleValve(id, isChecked) {
  await AgroAPI.toggleValve(id, isChecked);
}

function triggerSimulatedSMS() {
  const msg = currentSiteLanguage === 'en' 
    ? "AgroSmart Alert: Soil moisture level 78% optimal. Valve #1 running."
    : "உழவன் எச்சரிக்கை: தக்காளி தோட்டம் ஈரப்பதம் 78%. பாசனம் தேவையில்லை.";
  alert(`📱 SMS Sent (+91 98765 43210): '${msg}'`);
}

function scrollToVoiceAssistant() {
  document.getElementById('ai-assistant-card').scrollIntoView({ behavior: 'smooth' });
}

function scrollToCCTV() {
  document.getElementById('cctv-card').scrollIntoView({ behavior: 'smooth' });
}

function openAddProductModal() {
  const promptName = currentSiteLanguage === 'en' ? "Enter Product Name (e.g., Organic Capsicum):" : "விளைபொருள் பெயர் (எ.கா: குடைமிளகாய்):";
  const name = prompt(promptName);
  if (!name) return;

  const promptPrice = currentSiteLanguage === 'en' ? "Enter Price per kg in ₹:" : "கிலோவுக்கு விலை (ரூபாயில்):";
  const price = prompt(promptPrice, "60");
  if (!price) return;

  const promptStock = currentSiteLanguage === 'en' ? "Enter Stock in kg:" : "கையிருப்பு (கிலோவில்):";
  const stock = prompt(promptStock, "150");
  if (!stock) return;

  const perKgLabel = currentSiteLanguage === 'en' ? "per kg" : "கிலோவுக்கு";
  const stockLabel = currentSiteLanguage === 'en' ? "Stock" : "கையிருப்பு";

  const container = document.getElementById('products-list');
  const newCard = document.createElement('div');
  newCard.className = "flex items-center justify-between p-4 bg-stone-50 rounded-lg hover:bg-stone-100 transition-all border border-stone-100";
  newCard.innerHTML = `
    <div class="flex items-center space-x-4">
      <div class="text-3xl">🫑</div>
      <div>
        <h4 class="font-semibold text-stone-900">${name}</h4>
        <div class="flex items-center space-x-3 mt-1">
          <span class="text-base font-bold text-farm-700">₹${price} <span class="text-xs font-normal text-stone-500">${perKgLabel}</span></span>
          <span class="text-[11px] bg-farm-100 text-farm-800 font-medium px-2 py-0.5 rounded">Active</span>
        </div>
        <div class="flex items-center space-x-3 text-xs text-stone-400 mt-1">
          <span>${stockLabel}: ${stock} kg</span>
          <span>• 1 view</span>
          <span>• 5.0 ★</span>
        </div>
      </div>
    </div>
    <button class="text-xs border border-stone-300 px-3 py-1.5 rounded hover:bg-white text-stone-700 font-medium">Edit</button>
  `;
  container.prepend(newCard);
  const successMsg = currentSiteLanguage === 'en' ? `Added ${name} to your Marketplace inventory!` : `விளைபொருள் ${name} உங்கள் சந்தை பட்டியலில் சேர்க்கப்பட்டது!`;
  alert(successMsg);
}
