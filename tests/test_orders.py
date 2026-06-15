import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app
from src.database.connection import Base, engine, get_db
from src.modules.users.models import User
from src.modules.products.models import Product
from src.modules.categories.models import Category
from src.modules.cart.models import Cart, CartItem
from src.modules.orders.models import Order, OrderItem

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    
    # Create test category if not exists
    category = db.query(Category).filter(Category.name == "Test Order Cat").first()
    if not category:
        category = Category(
            name="Test Order Cat",
            description="Category for testing orders"
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        
    # Create test product if not exists
    product = db.query(Product).filter(Product.name == "Test Order Product").first()
    if not product:
        product = Product(
            name="Test Order Product",
            category_id=category.id,
            price=150.0,
            stock=100,
            is_active=True
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        
    yield db

def test_checkout_flow_cod(setup_db):
    db = setup_db
    
    # 1. Clean up user if they exist from previous test runs
    email = "checkout_test_cod@example.com"
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
        
    # 2. Register a test user
    reg_res = client.post(
        "/api/v1/users/",
        data={
            "first_name": "Checkout",
            "last_name": "User",
            "email": email,
            "password": "password123",
            "phone": "01700000000",
            "address": "123 Road, Dhaka"
        }
    )
    assert reg_res.status_code == 201
    
    # Make sure user is verified and active
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    user.is_verified = True
    user.is_active = True
    db.commit()
    
    # 2. Login to get JWT token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["tokens"]["access"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Get Product
    product = db.query(Product).filter(Product.name == "Test Order Product").first()
    assert product is not None
    
    # 4. Add product to cart
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()
        
    add_cart_res = client.post(
        "/api/v1/cart/items/",
        headers=headers,
        json={"product_id": product.id, "quantity": 2}
    )
    assert add_cart_res.status_code == 200
    
    # Record initial stock
    initial_stock = product.stock
    
    # 5. Checkout with COD
    checkout_res = client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={
            "shipping_address": "123 Road, Dhaka",
            "phone": "01700000000",
            "payment_method": "cod"
        }
    )
    assert checkout_res.status_code == 200
    order_data = checkout_res.json()
    assert order_data["status"] == "pending"
    assert order_data["payment_method"] == "cod"
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["product_id"] == product.id
    assert order_data["items"][0]["quantity"] == 2
    
    # 6. Verify cart is cleared & stock is decremented
    db.refresh(product)
    assert product.stock == initial_stock - 2
    
    cart_res = client.get("/api/v1/cart/", headers=headers)
    assert cart_res.status_code == 200
    assert len(cart_res.json()["items"]) == 0
    
    # 7. Mark order as paid manually
    order_id = order_data["id"]
    pay_res = client.post(f"/api/v1/orders/{order_id}/pay-success", headers=headers)
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "paid"

@patch("src.modules.orders.router.initiate_sslcommerz_payment")
def test_checkout_payment_methods(mock_ssl, setup_db):
    db = setup_db

    email = "payment_test@example.com"
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
        
    reg_res = client.post(
        "/api/v1/users/",
        data={
            "first_name": "Payment",
            "last_name": "User",
            "email": email,
            "password": "password123",
            "phone": "01711111111",
            "address": "456 Lane, Dhaka"
        }
    )
    assert reg_res.status_code == 201
    
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    user.is_verified = True
    user.is_active = True
    db.commit()
    
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"}
    )
    token = login_res.json()["tokens"]["access"]
    headers = {"Authorization": f"Bearer {token}"}
    
    product = db.query(Product).filter(Product.name == "Test Order Product").first()
    
    # Mocking SSLCommerz redirect URL
    mock_ssl.return_value = "http://mock-sslcommerz-redirect-url"

    # Test SSLCommerz
    client.post(
        "/api/v1/cart/items/",
        headers=headers,
        json={"product_id": product.id, "quantity": 1}
    )
    checkout_ssl = client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={
            "shipping_address": "456 Lane, Dhaka",
            "phone": "01711111111",
            "payment_method": "sslcommerz"
        }
    )
    assert checkout_ssl.status_code == 200
    assert checkout_ssl.json()["payment_url"] == "http://mock-sslcommerz-redirect-url"
