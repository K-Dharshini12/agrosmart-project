import uvicorn
import os
import sys

# Ensure backend folder is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting AgroSmart / Ulavan Connect AI Backend Server on http://127.0.0.1:8000 ...")
    print("Interactive Swagger API Docs available at http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
