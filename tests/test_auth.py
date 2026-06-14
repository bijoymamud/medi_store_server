from fastapi.testclient import TestClient
from src.main import app
from src.database.connection import Base, engine

client = TestClient(app)

def test_register_and_login():
    Base.metadata.create_all(bind=engine)
    
    # 1. Register User
    unique_email = "testauth@example.com"
    response = client.post(
        "/api/v1/users/",
        json={"email": unique_email, "password": "securepassword", "full_name": "Auth Tester"}
    )
    # Could be 201 or 400 if already exists
    assert response.status_code in [201, 400]
    
    # 2. Login (Before verification - should fail with 401 or succeed?)
    # Wait, in the router we only check is_active for login. is_verified is checked in the dependency get_current_active_verified_user.
    # So login itself will succeed.
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": "securepassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token is not None

def test_verify_email_failure():
    response = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "testauth@example.com", "otp": "000000"}
    )
    # The OTP is random, so 000000 will fail
    assert response.status_code == 400
    assert response.json()["detail"] in ["Invalid OTP", "OTP expired", "User already verified"]
