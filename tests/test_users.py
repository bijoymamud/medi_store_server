from fastapi.testclient import TestClient
from src.main import app
from src.database.connection import Base, engine

# For a simple integration test, we use the same database connection
# In a real setup, we should use an overridden in-memory SQLite dependency, 
# but we are just demonstrating the endpoint health here.

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Server is healthy"}

# Simple test that handles db tables being setup.
def test_create_user_invalid_email():
    response = client.post(
        "/api/v1/users/",
        json={"email": "not-an-email", "password": "password", "full_name": "Test User"}
    )
    # Pydantic validation should catch this
    assert response.status_code == 422
