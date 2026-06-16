from fastapi.testclient import TestClient
from src.main import app
from src.database.connection import Base, engine, SessionLocal
from src.modules.users.models import User
from src.modules.products.models import Product
from src.modules.categories.models import Category
from src.modules.cart.models import Cart, CartItem
from src.modules.orders.models import Order
from unittest.mock import patch

client = TestClient(app)

def test_rate_limiting_and_refresh_flow():
    Base.metadata.create_all(bind=engine)
    from src.modules.auth.router import login_limiter
    login_limiter.requests.clear()
    
    unique_email = "rate_limit_test@example.com"
    
    # 1. Register and activate user
    response = client.post(
        "/api/v1/users/",
        data={
            "first_name": "Rate",
            "last_name": "Limiter",
            "email": unique_email,
            "password": "securepassword",
            "address": "123 Test St",
            "phone": "01700000000"
        }
    )
    assert response.status_code in [201, 400]
    
    db = SessionLocal()
    db_user = db.query(User).filter(User.email == unique_email).first()
    if db_user:
        db_user.is_active = True
        db_user.is_verified = True
        db.commit()
    db.close()
    
    # 2. Test login and check refresh cookie set
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "securepassword"}
    )
    assert login_response.status_code == 200
    assert "refresh_token" in login_response.cookies
    assert login_response.json()["tokens"]["access"] is not None
    
    # 3. Test refresh token endpoint
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": login_response.cookies["refresh_token"]}
    )
    assert refresh_response.status_code == 200
    assert "refresh_token" in refresh_response.cookies
    assert refresh_response.json()["tokens"]["access"] is not None
    
    # 4. Test logout clears cookie
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    cookie_headers = logout_response.headers.get_list("set-cookie")
    assert any("refresh_token=" in h for h in cookie_headers)
    assert any("max-age=0" in h.lower() or "expires=" in h.lower() for h in cookie_headers)

    # 5. Test rate limiting triggers 429
    failed = False
    for _ in range(15):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "securepassword"}
        )
        if r.status_code == 429:
            failed = True
            break
            
    assert failed is True

@patch("src.modules.orders.router.initiate_sslcommerz_payment")
def test_checkout_payment_failure_stock_restoration(mock_ssl):
    # Setup database and clear previous user
    Base.metadata.create_all(bind=engine)
    from src.modules.auth.router import login_limiter
    login_limiter.requests.clear()
    
    db = SessionLocal()
    
    # 1. Clean up user if they exist
    email = "rollback_test@example.com"
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
        
    # 2. Register and verify user
    response = client.post(
        "/api/v1/users/",
        data={
            "first_name": "Rollback",
            "last_name": "Tester",
            "email": email,
            "password": "password123",
            "phone": "01700000000",
            "address": "123 Road, Dhaka"
        }
    )
    assert response.status_code == 201
    
    user = db.query(User).filter(User.email == email).first()
    user.is_verified = True
    user.is_active = True
    db.commit()
    
    # 3. Create test category and product if they don't exist
    category = db.query(Category).filter(Category.name == "Test Order Cat").first()
    if not category:
        category = Category(name="Test Order Cat", description="Cat")
        db.add(category)
        db.commit()
        db.refresh(category)
        
    product = db.query(Product).filter(Product.name == "Test Order Product").first()
    if not product:
        product = Product(name="Test Order Product", category_id=category.id, price=100.0, stock=50, is_active=True)
        db.add(product)
    else:
        product.stock = 50
    db.commit()
    db.refresh(product)
        
    initial_stock = product.stock
    
    # 4. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"}
    )
    token = login_res.json()["tokens"]["access"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 5. Add product to cart
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()
        
    client.post(
        "/api/v1/cart/items/",
        headers=headers,
        json={"product_id": product.id, "quantity": 3}
    )
    
    # 6. Mock SSLCommerz failure (returning None)
    mock_ssl.return_value = None
    
    # 7. Checkout (this should raise a 502 HTTP exception, since payment setup failed)
    checkout_res = client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={
            "shipping_address": "123 Road, Dhaka",
            "phone": "01700000000",
            "payment_method": "sslcommerz"
        }
    )
    
    assert checkout_res.status_code == 502
    assert "Failed to initialize SSLCommerz payment" in checkout_res.json()["detail"]
    
    # 8. Verify order status is failed and product stock has been restored
    db.refresh(product)
    assert product.stock == initial_stock  # stock restored to initial_stock (not decremented by 3)
    
    # Check that a failed order was created
    order = db.query(Order).filter(Order.user_id == user.id).first()
    assert order is not None
    assert order.status == "cancelled"
    db.close()

def test_security_headers():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
