from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_get_special_offers_public():
    response = client.get("/api/v1/special-offers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
