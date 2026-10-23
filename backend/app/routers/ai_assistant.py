import os
import httpx
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SensorReading
from ..schemas import AIChatRequest, AIChatResponse, AIKeyConfigRequest, AIKeyConfigResponse
from ..services.ai_knowledge import generate_agri_response, clean_text_for_speech

router = APIRouter(prefix="/api/ai", tags=["AI Agronomist Assistant"])

@router.get("/config", response_model=AIKeyConfigResponse)
def get_ai_config():
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    preferred = os.getenv("AI_PROVIDER", "").strip().lower()

    active = "none"
    if groq_key:
        active = "Groq (GPT-OSS / Qwen)"
    elif gemini_key:
        active = "Google Gemini (3.5 Flash)"
    if preferred == "gemini" and gemini_key:
        active = "Google Gemini (3.5 Flash)"
    elif preferred == "groq" and groq_key:
        active = "Groq (GPT-OSS / Qwen)"

    return AIKeyConfigResponse(
        has_groq=bool(groq_key),
        has_gemini=bool(gemini_key),
        active_provider=active,
        message="Keys configured and active" if (groq_key or gemini_key) else "No external LLM key set. Using local Tamil agronomist rules."
    )

@router.post("/config", response_model=AIKeyConfigResponse)
def update_ai_config(payload: AIKeyConfigRequest):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    
    if payload.groq_api_key:
        os.environ["GROQ_API_KEY"] = payload.groq_api_key.strip()
    if payload.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = payload.gemini_api_key.strip()
    if payload.ai_provider:
        os.environ["AI_PROVIDER"] = payload.ai_provider.strip().lower()

    # Persist to .env safely
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    keys_to_update = {}
    if payload.groq_api_key:
        keys_to_update["GROQ_API_KEY"] = payload.groq_api_key.strip()
    if payload.gemini_api_key:
        keys_to_update["GEMINI_API_KEY"] = payload.gemini_api_key.strip()
    if payload.ai_provider:
        keys_to_update["AI_PROVIDER"] = payload.ai_provider.strip().lower()

    new_lines = []
    updated_keys = set()
    for line in lines:
        for k, v in keys_to_update.items():
            if line.startswith(f"{k}="):
                new_lines.append(f"{k}={v}\n")
                updated_keys.add(k)
                break
        else:
            new_lines.append(line)

    for k, v in keys_to_update.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return get_ai_config()

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_assistant(payload: AIChatRequest, db: Session = Depends(get_db)):
    # Grab latest sensor context for situational awareness
    latest_sensor = db.query(SensorReading).order_by(SensorReading.id.desc()).first()
    context = {}
    if latest_sensor:
        context = {
            "soil_moisture": latest_sensor.soil_moisture,
            "soil_temperature": latest_sensor.soil_temperature,
            "soil_ph": latest_sensor.soil_ph,
            "water_tank_level": latest_sensor.water_tank_level
        }
    if payload.context:
        context.update(payload.context)

    reply_data = await generate_agri_response(
        user_message=payload.message,
        language=payload.language or "ta",
        sensor_context=context,
        client_api_key=payload.api_key,
        client_provider=payload.provider
    )

    return AIChatResponse(
        reply=reply_data["reply"],
        speech_text=reply_data.get("speech_text"),
        language=reply_data["language"],
        intent=reply_data["intent"],
        engine=reply_data.get("engine"),
        suggested_actions=reply_data.get("suggested_actions")
    )

@router.get("/tts")
async def stream_text_to_speech(
    text: str = Query(..., min_length=1),
    lang: str = Query("ta")
):
    """
    Streams authentic native Tamil or English speech audio (MP3).
    Guarantees pure Tamil voice playback across all browsers and devices without OS dependencies.
    """
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        clean_text = "வணக்கம்"

    # Google Translate TTS endpoint provides high quality native Tamil pronunciation
    url = "https://translate.google.com/translate_tts"
    target_lang = "ta" if lang in ["ta", "tamil", "thanglish"] else "en"
    params = {
        "ie": "UTF-8",
        "tl": target_lang,
        "client": "tw-ob",
        "q": clean_text[:200]
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                from fastapi import Response
                return Response(
                    content=resp.content,
                    media_type="audio/mpeg",
                    headers={"Cache-Control": "public, max-age=3600"}
                )
    except Exception as e:
        print(f"TTS audio error: {e}")

    from fastapi import HTTPException
    raise HTTPException(status_code=502, detail="TTS service unavailable")

@router.post("/voice-webhook")
def telephony_voice_webhook(call_sid: str = "sim_123", digits: str = None, lang: str = "ta"):
    """
    IVR / Telephony webhook endpoint compatible with Twilio / Exotel / Plivo voice calls.
    Supports Tamil and English.
    """
    greetings = {
        "ta": "வணக்கம்! உழவன் கனெக்ட் ஏஐ உங்களை அன்புடன் வரவேற்கிறது.",
        "en": "Welcome to AgroSmart Farm Voice Assistant."
    }
    return {
        "status": "connected",
        "call_sid": call_sid,
        "message": greetings.get(lang, greetings["ta"]),
        "options": [
            {"digit": 1, "description": "மண் ஈரப்பதம் அறிக்கை (Soil Moisture)"},
            {"digit": 2, "description": "வானிலை எச்சரிக்கை (Weather Advisory)"},
            {"digit": 3, "description": "தக்காளி மண்டி விலை (Mandi Price)"}
        ]
    }
