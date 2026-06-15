from fastapi.testclient import TestClient
from src.main import app
from src.database.connection import Base, engine, SessionLocal
from src.modules.users.models import User

client = TestClient(app)

def test_contact_flow():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Ensure a test admin user exists
    admin_email = "contactadmin@example.com"
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if not admin_user:
        from src.modules.users.router import get_password_hash
        admin_user = User(
            email=admin_email,
            full_name="Contact Admin",
            hashed_password=get_password_hash("adminpassword"),
            phone="01700000000",
            address="Admin HQ",
            is_active=True,
            is_verified=True,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
    db.close()

    # 1. Post a Support Request (Public access)
    payload = {
        "client_name": "Dr. Watson",
        "email": "watson@bakerstreet.com",
        "department": "Diagnostic & Imaging",
        "specifications": "Requesting quote for portable ultrasound machines."
    }
    
    response = client.post("/api/v1/contact/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["client_name"] == payload["client_name"]
    assert data["email"] == payload["email"]
    assert data["department"] == payload["department"]
    assert data["specifications"] == payload["specifications"]

    # 2. Get list as anonymous user (should fail)
    list_anon_resp = client.get("/api/v1/contact/")
    assert list_anon_resp.status_code == 401

    # 3. Login as admin and get list (should succeed)
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "adminpassword"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["tokens"]["access"]
    
    list_admin_resp = client.get(
        "/api/v1/contact/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_admin_resp.status_code == 200
    requests_list = list_admin_resp.json()
    assert len(requests_list) > 0
    # The submitted request should be in the list
    watson_request = next((r for r in requests_list if r["client_name"] == "Dr. Watson"), None)
    assert watson_request is not None
    assert watson_request["specifications"] == payload["specifications"]
