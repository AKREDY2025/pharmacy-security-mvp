from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="PharmSecure Security MVP")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok", "message": "PharmSecure API is running"}

# Welcome endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to PharmSecure Security MVP"}

# Verification endpoint (mock)
@app.post("/api/v1/verify")
async def verify_product(serial_number: str):
    return {
        "serial_number": serial_number,
        "result": "AUTHENTIC",
        "confidence_score": 0.95,
        "message": "Product verified successfully"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
