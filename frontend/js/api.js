const API_HOST = (window.location.port === "8000" || window.location.port === "")
  ? window.location.origin
  : "http://127.0.0.1:8000";
const API_BASE_URL = `${API_HOST}/api`;
const WS_BASE_URL = (window.location.port === "8000" || window.location.port === "")
  ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/iot/ws`
  : "ws://127.0.0.1:8000/api/iot/ws";

window.AGRO_API_HOST = API_HOST;
window.AGRO_API_BASE_URL = API_BASE_URL;

const AgroAPI = {
  // Telemetry
  async getLatestTelemetry() {
    try {
      const res = await fetch(`${API_BASE_URL}/iot/latest`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("Backend telemetry offline, using fallback");
    }
    return {
      soil_moisture: 78,
      soil_temperature: 24,
      soil_ph: 6.8,
      water_tank_level: 1250,
      connectivity_status: "online",
      lora_rssi: -65
    };
  },

  // Actuator Valves
  async getValves() {
    try {
      const res = await fetch(`${API_BASE_URL}/controls/valves`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("Backend valves offline, using fallback");
    }
    return [
      { id: 1, name: "Main Irrigation Valve", zone_name: "Tomato Field A", is_open: true, flow_rate: "15 L/min" },
      { id: 2, name: "Secondary Valve", zone_name: "Vegetable Field B", is_open: false, flow_rate: "8 L/min" }
    ];
  },

  async toggleValve(id, isOpen) {
    try {
      const res = await fetch(`${API_BASE_URL}/controls/valves/${id}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_open: isOpen })
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.log(`Local toggle valve ${id} to ${isOpen}`);
    }
    return { id, is_open: isOpen };
  },

  // AI Chat with Groq & Gemini (keys handled securely in backend .env)
  async chatWithAI(message, language = "ta", context = null) {
    try {
      const res = await fetch(`${API_BASE_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          language,
          context
        })
      });
      if (res.ok) {
        return await res.json();
      } else {
        const errText = await res.text();
        console.error("AI Chat API Error:", res.status, errText);
      }
    } catch (e) {
      console.warn("Backend offline or CORS blocked:", e);
    }
    return null;
  },

  // Marketplace
  async getProducts() {
    try {
      const res = await fetch(`${API_BASE_URL}/marketplace/products`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return null;
  },

  async getMandiPrices() {
    try {
      const res = await fetch(`${API_BASE_URL}/marketplace/mandi-prices`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return null;
  },

  async getBuyers() {
    try {
      const res = await fetch(`${API_BASE_URL}/marketplace/buyers`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return null;
  },

  // CCTV
  async getCctvStatus() {
    try {
      const res = await fetch(`${API_BASE_URL}/cctv/status`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return {
      is_live: false,
      camera_name: "No CCTV Connected",
      growth_analysis: "No Signal",
      pest_detection: "Disconnected",
      harvest_ready: "Offline"
    };
  },

  async connectCctv(payload) {
    try {
      const res = await fetch(`${API_BASE_URL}/cctv/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("CCTV connect request failed:", e);
    }
    return { is_live: true, camera_name: payload.camera_name || "Live Farm CCTV" };
  },

  async disconnectCctv() {
    try {
      const res = await fetch(`${API_BASE_URL}/cctv/disconnect`, {
        method: "POST"
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("CCTV disconnect request failed:", e);
    }
    return { is_live: false };
  },

  // Weather & Locations
  async getPopularPlaces() {
    try {
      const res = await fetch(`${API_BASE_URL}/weather/places`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return [];
  },

  async searchPlaces(query) {
    try {
      const res = await fetch(`${API_BASE_URL}/weather/search?query=${encodeURIComponent(query)}`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return [];
  },

  async getLivePlaceWeather(place, lat, lon) {
    try {
      const res = await fetch(`${API_BASE_URL}/weather/live?place=${encodeURIComponent(place)}&lat=${lat}&lon=${lon}`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return null;
  },

  // WebSocket Live Sync
  initWebSocket(onTelemetryUpdate) {
    try {
      const ws = new WebSocket(WS_BASE_URL);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === "TELEMETRY_UPDATE") {
            onTelemetryUpdate(msg.data);
          }
        } catch (err) {}
      };
      ws.onerror = () => console.log("WebSocket running in polling mode.");
    } catch (err) {}
  }
};
