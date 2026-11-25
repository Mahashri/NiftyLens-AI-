from fastapi.testclient import TestClient
from backend.main import app

def test_health():
    with TestClient(app) as client:
        r=client.get("/api/health")
        assert r.status_code==200 and r.json()["status"]=="ok"

def test_invalid_symbol():
    with TestClient(app) as client:
        assert client.get("/api/stocks/BAD%20SYMBOL").status_code==400
