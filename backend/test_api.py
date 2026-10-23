import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_system():
    # 1. Healthcheck
    res = client.get("/")
    assert res.status_code == 200
    print("Healthcheck:", res.json())

    # 2. Check AI Configuration
    res = client.get("/api/ai/config")
    assert res.status_code == 200
    print("AI Config Status:", res.json())

    # 3. Test Pure Tamil
    res = client.post("/api/ai/chat", json={"message": "தக்காளிக்கு என்ன உரம் போடலாம்?", "language": "ta"})
    assert res.status_code == 200
    reply = res.json()
    print("\n[Test 1 - Pure Tamil]:", reply["intent"], "->", reply["reply"][:80], "...")

    # 4. Test Colloquial Tamil
    res = client.post("/api/ai/chat", json={"message": "மண்ணுல தண்ணி இருக்கா பாய்ச்சலாமா?", "language": "ta"})
    assert res.status_code == 200
    reply = res.json()
    print("\n[Test 2 - Colloquial Tamil]:", reply["intent"], "->", reply["reply"][:80], "...")

    # 5. Test Thanglish - Soil Moisture ("Thanni paachalama bro?")
    res = client.post("/api/ai/chat", json={"message": "Thanni paachalama bro? Mann eeram eppadi irukku?", "language": "ta"})
    assert res.status_code == 200
    reply = res.json()
    print("\n[Test 3 - Thanglish Water]:", reply["intent"], "->", reply["reply"][:80], "...")

    # 6. Test Thanglish - Pest Control ("Poochi thollai jaasthi ah irukku")
    res = client.post("/api/ai/chat", json={"message": "Thakkali chediyila poochi thollai jaasthi ah irukku enna marunthu spray pannalam?", "language": "ta"})
    assert res.status_code == 200
    reply = res.json()
    print("\n[Test 4 - Thanglish Pest]:", reply["intent"], "->", reply["reply"][:80], "...")

    # 7. Test Thanglish - Mandi Price ("Thakkali rate enna ippo?")
    res = client.post("/api/ai/chat", json={"message": "Thakkali rate enna ippo mandiyila?", "language": "ta"})
    assert res.status_code == 200
    reply = res.json()
    print("\n[Test 5 - Thanglish Price]:", reply["intent"], "->", reply["reply"][:80], "...")

    # 8. Test English
    res = client.post("/api/ai/chat", json={"message": "What is my soil moisture today?", "language": "en"})
    assert res.status_code == 200
    reply = res.json()
    print("\n[Test 6 - English]:", reply["intent"], "->", reply["reply"][:80], "...")

    print("\nALL TAMIL, THANGLISH, ENGLISH, AND API KEY CONFIG TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_system()
