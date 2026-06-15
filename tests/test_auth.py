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
        data={
            "first_name": "Auth",
            "last_name": "Tester",
            "email": unique_email,
            "password": "securepassword",
            "address": "123 Test St",
            "phone": "01700000000"
        }
    )
    # Could be 201 or 400 if already exists
    assert response.status_code in [201, 400]
    
    # 2. Activate user in DB directly so they can log in
    from src.database.connection import SessionLocal
    from src.modules.users.models import User
    db = SessionLocal()
    db_user = db.query(User).filter(User.email == unique_email).first()
    if db_user:
        db_user.is_active = True
        db_user.is_verified = True
        db.commit()
    db.close()

    # 3. Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "securepassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["tokens"]["access"]
    assert token is not None

def test_verify_email_failure():
    response = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "testauth@example.com", "otp": "000000"}
    )
    # The OTP is random, so 000000 will fail
    assert response.status_code == 400
    assert response.json()["detail"] in ["Invalid OTP", "OTP expired", "User already verified"]
