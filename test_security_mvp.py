import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_welcome():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_verify_authentic():
    response = client.post("/api/v1/verify?serial_number=AX-2024-001234")
    assert response.status_code == 200
    assert response.json()["result"] == "AUTHENTIC"

def test_verify_counterfeit():
    response = client.post("/api/v1/verify?serial_number=FAKE-999")
    assert response.status_code == 200
    assert "result" in response.json()

