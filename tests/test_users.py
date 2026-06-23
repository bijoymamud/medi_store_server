from fastapi.testclient import TestClient
from src.main import app
from src.database.connection import Base, engine, SessionLocal
from src.modules.users.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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

def test_admin_create_user():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Clean up any previous test users if they exist
    db.query(User).filter(User.email.in_(["admin_tester@example.com", "new_user_via_admin@example.com", "new_admin_via_admin@example.com"])).delete(synchronize_session=False)
    db.commit()
    
    # 2. Create an admin user directly in DB
    hashed = pwd_context.hash("adminpassword")
    admin_user = User(
        email="admin_tester@example.com",
        hashed_password=hashed,
        full_name="Admin Tester",
        is_active=True,
        is_verified=True,
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # 3. Login as admin
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin_tester@example.com", "password": "adminpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["tokens"]["access"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 4. Use admin_create_user endpoint to create a Customer
    response_user = client.post(
        "/api/v1/users/admin/create",
        headers=headers,
        json={
            "email": "new_user_via_admin@example.com",
            "password": "userpass123",
            "role": "user",
            "full_name": "New Customer",
            "phone": "01711223344",
            "address": "Dhaka, Bangladesh"
        }
    )
    assert response_user.status_code == 201
    user_data = response_user.json()
    assert user_data["email"] == "new_user_via_admin@example.com"
    assert user_data["is_admin"] is False
    assert user_data["is_active"] is True
    
    # 5. Use admin_create_user endpoint to create another Admin
    response_admin = client.post(
        "/api/v1/users/admin/create",
        headers=headers,
        json={
            "email": "new_admin_via_admin@example.com",
            "password": "adminpass123",
            "role": "admin",
            "full_name": "New Admin"
        }
    )
    assert response_admin.status_code == 201
    admin_data = response_admin.json()
    assert admin_data["email"] == "new_admin_via_admin@example.com"
    assert admin_data["is_admin"] is True
    assert admin_data["is_active"] is True
    
    # 6. Test unauthorized access (no headers)
    response_unauth = client.post(
        "/api/v1/users/admin/create",
        json={
            "email": "no_header@example.com",
            "password": "password123",
            "role": "user"
        }
    )
    assert response_unauth.status_code == 401
    
    db.close()

