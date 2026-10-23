import os
import re
import json
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

# Fallback pre-computed responses when no LLM API key is present
KNOWLEDGE_RESPONSES = {
    "en": {
        "greeting": "Vanakkam! I'm your AgroSmart Tamil & English farm assistant. Ask me anything about soil moisture, weather, pests, tomato prices, or fertilizers in Tamil, Thanglish, or English!",
        "soilMoisture": "Your live soil moisture is at 78%, which is optimal for tomato crops. Drip irrigation does not need to be triggered right now.",
        "weather": "Tomorrow's forecast predicts rain in your region. It is recommended to reduce irrigation by 50% to prevent root rot and waterlogging.",
        "pests": "Early aphid symptoms detected on lower tomato foliage. Spray 5ml neem oil (வேப்பெண்ணெய்) mixed with 1ml liquid soap per liter of water early morning or late evening.",
        "harvest": "Based on current color-break staging and vegetative growth index, your tomatoes will reach peak harvest readiness in 5 to 7 days.",
        "price": "Current APMC Mandi tomato price is ₹85/kg with strong wholesale demand. High market advantage for immediate harvest planning.",
        "irrigation": "Automated valve #1 is operating at 15 L/min for Tomato Field A. Soil saturation is healthy.",
        "fertilizer": "For the flowering to fruiting stage, apply NPK 13:0:45 or 0:52:34 along with Micronutrient mix via fertigation for high fruit setting."
    },
    "ta": {
        "greeting": "வணக்கம் உழவர் பெருமக்களே! நான் உங்களின் உழவன் ஏஐ (AgroSmart) உதவியாளர். மண் ஈரப்பதம், மழை நிலவரம், உரம், பூச்சி மேலாண்மை, தக்காளி சந்தை விலை பற்றி தூய தமிழ், பேச்சுத் தமிழ் அல்லது தங்க்லீஷில் (Thanglish) கேளுங்கள்!",
        "soilMoisture": "உங்கள் தோட்டத்தின் மண் ஈரப்பதம் தற்போது 78% ஆக உள்ளது. இது தக்காளி செடிகளுக்கு மிகவும் உகந்த அளவு. இப்போது தண்ணீர் பாய்ச்ச தேவையில்லை.",
        "weather": "நாளை உங்கள் பகுதியில் மழை பெய்ய வாய்ப்புள்ளது. வேர் அழுகல் மற்றும் நீர் தேங்குவதை தடுக்க நீர்ப்பாசனத்தை 50% குறைத்துக் கொள்ளவும்.",
        "pests": "தக்காளி இலைகளில் அசுவினி மற்றும் சாறு உறிஞ்சும் பூச்சிகள் தென்படுகின்றன. ஒரு லிட்டர் தண்ணீருக்கு 5 மிலி வேப்பெண்ணெய் மற்றும் 1 மிலி காதி சோப் கரைசல் கலந்து அதிகாலை அல்லது மாலை வேளையில் தெளிக்கவும்.",
        "harvest": "பழங்களின் நிற மாற்றத்தின்படி இன்னும் 5 முதல் 7 நாட்களில் தக்காளி அறுவடைக்கு முழுமையாக தயாராகிவிடும்.",
        "price": "இன்றைய மண்டி நிலவரப்படி தக்காளி கிலோவுக்கு ₹85 வரை நல்ல விலைக்கு போகிறது. நல்ல கிராக்கி இருப்பதால் அறுவடை செய்து விற்பனைக்கு அனுப்ப உகந்த நேரம்!",
        "irrigation": "தக்காளி பிரிவு A க்கான முதன்மை வால்வு 15 L/min வேகத்தில் இயங்குகிறது. மண் போதுமான ஈரப்பதத்துடன் உள்ளது.",
        "fertilizer": "பூ மற்றும் காய் பிடிக்கும் பருவத்தில் பொட்டாசியம் மற்றும் பாஸ்பரஸ் தேவை அதிகம். 19:19:19 அல்லது 0:52:34 நீரில் கரையும் உரத்தை சொட்டுநீர் மூலம் கொடுக்கலாம்."
    }
}

THANGLISH_INTENT_PATTERNS = {
    "soilMoisture": [
        "thanni", "thani", "eeram", "eerappatham", "moisture", "mann", "soil", "paachalama", "paaikalama",
        "water level", "mannu", "mann eeram"
    ],
    "weather": [
        "mazhai", "malai", "rain", "weather", "kaathu", "vanilai", "vaanilai", "nalaiku mazhai", "tomorrow rain"
    ],
    "pests": [
        "poochi", "puchi", "keera", "ilai pulli", "pest", "disease", "marunthu", "spray", "neem oil", "insect",
        "ilai karuguthu", "ilai suruluthu", "sokku"
    ],
    "harvest": [
        "aruvadai", "aruvada", "arukalama", "harvest", "parikkalama", "eppothu arukka", "ready", "ripe", "palam"
    ],
    "price": [
        "rate", "vilai", "price", "mandi", "santhai", "kasu", "market", "evlo poguthu", "thakkali rate"
    ],
    "fertilizer": [
        "uram", "fertilizer", "npk", "urea", "potash", "manure", "sathu", "valarchi"
    ]
}

def analyze_intent(text: str) -> str:
    query = text.lower()
    
    # Check Tamil script
    if any(k in query for k in ["ஈரப்பதம்", "மண்", "தண்ணீர்", "நீர்ப்பாசனம்", "பாசனம்"]):
        return "soilMoisture"
    elif any(k in query for k in ["மழை", "வானிலை", "வெயில்", "காற்று"]):
        return "weather"
    elif any(k in query for k in ["பூச்சி", "நோய்", "மருந்து", "வேப்பெண்ணெய்", "புழு", "அசுவினி"]):
        return "pests"
    elif any(k in query for k in ["அறுவடை", "பறிக்கலாமா", "காய்", "பழம்"]):
        return "harvest"
    elif any(k in query for k in ["விலை", "சந்தை", "மண்டி", "ரேட்"]):
        return "price"
    elif any(k in query for k in ["உரம்", "சத்து", "யூரியா", "பொட்டாஷ்"]):
        return "fertilizer"

    # Check Thanglish & English keywords
    for intent, patterns in THANGLISH_INTENT_PATTERNS.items():
        if any(p in query for p in patterns):
            return intent

    return "greeting"

def build_system_prompt(sensor_context: Optional[Dict[str, Any]] = None) -> str:
    ctx_str = ""
    place_name = "Tamil Nadu"
    if sensor_context:
        place_name = sensor_context.get("location", "Tamil Nadu")
        ctx_str = f"""
CURRENT LIVE FARM & LOCATION CONTEXT:
- Farm Location: {place_name}
- Live Weather: {sensor_context.get('weather_condition', 'Sunny & Clear')}, Temp: {sensor_context.get('air_temperature', 28)}°C, Humidity: {sensor_context.get('humidity', 65)}%
- Rain Probability Tomorrow: {sensor_context.get('rain_probability', '85%')}
- Soil Moisture: {sensor_context.get('soil_moisture', 78)}% (Target: 65-80%)
- Root Soil Temperature: {sensor_context.get('soil_temperature', 24)}°C
- Soil pH: {sensor_context.get('soil_ph', 6.8)} (Optimal 6.0 - 7.0)
- Water Storage Tank: {sensor_context.get('water_tank_level', 1250)} Liters
- Irrigation Valve #1: Active (Flow 15 L/min)
- Current Tomato Market Mandi Rate: ₹85/kg
"""
    return f"""You are 'உழவன் தோழன்' (Uzhavan Thozhan / AgroSmart Agronomist AI), an expert agricultural scientist and direct field advisor for farmers in {place_name} and across Tamil Nadu.

{ctx_str}

STRICT DOMAIN RULE:
- You ONLY advise on FARMING, AGRICULTURE, CROPS, SOIL, IRRIGATION, PESTS, WEATHER, AND MANDI MARKET COMMODITY PRICES.
- NEVER talk about cooking, food recipes, breakfast dishes, or non-farming topics.
- Under NO circumstance interpret Tamil farming questions as cooking or snacks!

CRITICAL TAMIL AGRICULTURAL VOCABULARY:
1. "uram" / "உரம்" = FERTILIZER / Plant nutrient (e.g. NPK 19:19:19, DAP, Potash, Urea, வேப்பம் புண்ணாக்கு / Neem cake, தொழு உரம் / Compost, பஞ்சகவ்யா / Panchagavya, நுண்ணூட்ட உரம்). It is NEVER a food dish!
2. "thanni" / "thani" / "paasanam" / "பாசனம்" / "ஈரப்பதம்" = IRRIGATION / Soil watering / Drip irrigation.
3. "marunthu" / "spray" / "poochi" / "பூச்சி" = CROP PEST & DISEASE CONTROL (aphids, fruit borer, leaf miner, neem oil spray, fungicide).
4. "vilai" / "rate" / "மண்டி" = APMC Mandi wholesale crop market rate.
5. "thakkali" = Tomato crop. "vengayam" = Onion crop. "kathiri" = Brinjal. "nellu" = Paddy.
6. "aruvadai" / "அறுவடை" = Harvesting.

HOW TO ANSWER (CRITICAL FOR VOICE & CHAT RELEVANCE):
- Give DIRECT, PRACTICAL, HIGHLY RELEVANT farming answers.
- Keep responses CONCISE (2 to 4 sentences max).
- CRITICAL FOR VOICE & SPEECH: NEVER use formatting symbols like '#', '##', '###', '**', '*', '-', '_', or numbered lists like '1.', '2.'. Write in natural flowing plain sentences with periods and commas only, so text-to-speech voice assistant reads smoothly without saying 'hash' or 'dash'.
- If asked in Tamil or Thanglish (e.g., "thakkali uram enna podanum?"), reply in warm, respectful spoken Tamil (இயல்பான பேச்சுத் தமிழ்).
- If asked in English, reply in crisp practical English.
- Use the live sensor figures and weather context above whenever asked about watering, rain, soil, or prices.
"""

def clean_text_for_speech(raw: str) -> str:
    if not raw:
        return ""
    # Strip markdown code blocks & links
    clean = re.sub(r'```[\s\S]*?```', '', raw)
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
    # Strip symbols: * # _ ~ ` > | ( ) [ ] { }
    clean = re.sub(r'[*#_~`>|\(\)\[\]\{\}]', '', clean)
    # Strip bullet hyphens, bullets, and numbered prefixes like "1.", "2."
    clean = re.sub(r'^\s*[-•*]\s+', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'\s*-\s*', ' ', clean)
    clean = re.sub(r'\b\d+\.\s*', '', clean)
    # Replace colons with commas so voice engines pause naturally instead of saying "colon"
    clean = re.sub(r'[:]', ',', clean)
    # Normalize spaces
    clean = ' '.join(clean.split())
    # Limit to 2-3 sentences max for snappy speech
    sentences = re.split(r'(?<=[.?!।])\s+', clean)
    if len(sentences) > 3:
        clean = ' '.join(sentences[:3])
    return clean[:250].strip()

async def call_groq_llm(user_message: str, system_prompt: str, api_key: str) -> Optional[tuple]:
    """Call Groq API using available high-capacity models with automatic fallback."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    candidate_models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b"
    ]
    for model in candidate_models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.4,
            "max_tokens": 400
        }
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return (content, f"Groq ({model})")
                elif resp.status_code != 404:
                    print(f"[Groq Error on {model}] status: {resp.status_code}, body: {resp.text[:150]}")
        except Exception as e:
            print(f"[Groq Exception on {model}] {e}")
    return None

async def call_gemini_llm(user_message: str, system_prompt: str, api_key: str) -> Optional[tuple]:
    """Call Google Gemini using latest active models with automatic fallback."""
    candidate_models = [
        "gemini-3.5-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest"
    ]
    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_message}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 400
            }
        }
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return (parts[0]["text"], f"Google Gemini ({model})")
                elif resp.status_code not in [404, 503]:
                    print(f"[Gemini Error on {model}] status: {resp.status_code}, body: {resp.text[:150]}")
        except Exception as e:
            print(f"[Gemini Exception on {model}] {e}")
    return None

async def generate_agri_response(
    user_message: str,
    language: str = "ta",
    sensor_context: Optional[Dict[str, Any]] = None,
    client_api_key: Optional[str] = None,
    client_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for generating agricultural advice.
    Checks:
    1. Client provided API key (Groq or Gemini)
    2. Environment GROQ_API_KEY
    3. Environment GEMINI_API_KEY
    4. Smart domain rule fallback (Tamil / English)
    """
    system_prompt = build_system_prompt(sensor_context)
    intent = analyze_intent(user_message)

    # 1. Determine key & provider
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()

    active_provider = client_provider or os.getenv("AI_PROVIDER", "").lower()
    
    # If client passed an explicit key in request:
    if client_api_key:
        if client_api_key.startswith("gsk_") or active_provider == "groq":
            groq_key = client_api_key
            active_provider = "groq"
        elif client_api_key.startswith("AIza") or active_provider == "gemini":
            gemini_key = client_api_key
            active_provider = "gemini"

    # Attempt LLM generation
    llm_reply = None
    engine_used = "local-knowledge-base"

    # Strategy: Try preferred or available LLM
    res = None
    if active_provider == "groq" and groq_key:
        res = await call_groq_llm(user_message, system_prompt, groq_key)
    elif active_provider == "gemini" and gemini_key:
        res = await call_gemini_llm(user_message, system_prompt, gemini_key)
    
    # Fallback to the other provider if preferred failed or unset
    if not res:
        if groq_key:
            res = await call_groq_llm(user_message, system_prompt, groq_key)
        if not res and gemini_key:
            res = await call_gemini_llm(user_message, system_prompt, gemini_key)

    if res:
        llm_reply, engine_used = res

    if llm_reply:
        return {
            "reply": llm_reply,
            "speech_text": clean_text_for_speech(llm_reply),
            "language": language,
            "intent": intent,
            "engine": engine_used,
            "suggested_actions": ["சொட்டுநீர் பாசனம் சரிபார்க்கவும்", "வானிலை எச்சரிக்கை பார்க்கவும்", "சந்தை விலை பட்டியல்"]
        }

    # Fallback to local high-quality rule response
    target_lang = "ta" if language in ["ta", "tamil", "thanglish"] else "en"
    # If message is Thanglish, reply in friendly Tamil
    reply_template = KNOWLEDGE_RESPONSES[target_lang].get(intent, KNOWLEDGE_RESPONSES[target_lang]["greeting"])

    # Live telemetry insertion if requested
    if sensor_context and intent == "soilMoisture":
        curr_moisture = sensor_context.get("soil_moisture", 78)
        if target_lang == "ta":
            reply_template = f"நேரலை சென்சார் தகவல்: உங்கள் தக்காளி தோட்டத்தின் மண் ஈரப்பதம் தற்போது {curr_moisture}% ஆக உள்ளது. தக்காளி பயிருக்கு 65% முதல் 80% வரை உகந்தது. தற்போது தண்ணீர் பாய்ச்ச தேவையில்லை."
        else:
            reply_template = f"Live Telemetry: Your soil moisture is currently at {curr_moisture}%. The optimal target range for tomatoes is 65% to 80%. No irrigation is required at this time."

    return {
        "reply": reply_template,
        "speech_text": clean_text_for_speech(reply_template),
        "language": target_lang,
        "intent": intent,
        "engine": "Local Tamil Agronomist Engine (Add Groq or Gemini API key for full generative AI)",
        "suggested_actions": ["மண் ஈரப்பதம்", "மழை முன்னறிவிப்பு", "தக்காளி விலை"]
    }
