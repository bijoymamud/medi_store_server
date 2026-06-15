from fastapi import FastAPI
from src.database.connection import engine, Base
from src.modules.users import router as users_router
from src.modules.auth import router as auth_router
from src.modules.accounts import router as accounts_router
from src.modules.categories import router as categories_router
from src.modules.products import router as products_router
from src.modules.cart import router as cart_router
from src.modules.orders import router as orders_router
from src.modules.contact import router as contact_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

Base.metadata.create_all(bind=engine)

os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="MediStore API")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://10.10.13.99:5173", "http://10.10.13.99:8010"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(accounts_router.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(categories_router.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(products_router.router, prefix="/api/v1/products", tags=["products"])
app.include_router(cart_router.router, prefix="/api/v1/cart", tags=["cart"])
app.include_router(orders_router.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(contact_router.router, prefix="/api/v1/contact", tags=["contact"])

@app.get("/health")
def health_check():
    return {"status": "success", "message": "Server is healthy"}
