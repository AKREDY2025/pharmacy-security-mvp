from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
from pathlib import Path

SECRET_KEY = "pharmsecure-dev-key-2024"
ALGORITHM = "HS256"

app = FastAPI(
    title="PharmSecure Security MVP",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

class LoginRequest(BaseModel):
    username: str
    password: str

class VerifyRequest(BaseModel):
    serial_number: str

DEMO_USERS = {
    "pharmacy@ghs.com": "demo123",
    "manager@pharma.com": "password123",
    "test@pharmacy.com": "test123"
}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "PharmSecure API is running"}

@app.get("/")
def welcome():
    return {"message": "Welcome to PharmSecure Security MVP"}

@app.post("/login")
def login(credentials: LoginRequest):
    if credentials.username not in DEMO_USERS:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if DEMO_USERS[credentials.username] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    payload = {
        "username": credentials.username,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": credentials.username
    }

@app.post("/api/v1/verify")
def verify_product(request: VerifyRequest, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    serial = request.serial_number
    
    if "FAKE" in serial or "DUPLICATE" in serial or "999" in serial:
        result = "COUNTERFEIT"
        confidence = 0.92
        message = "⚠️ WARNING: Counterfeit product detected!"
    else:
        result = "AUTHENTIC"
        confidence = 0.95
        message = "✅ Product verified successfully"
    
    return {
        "serial_number": serial,
        "result": result,
        "confidence_score": confidence,
        "message": message
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
