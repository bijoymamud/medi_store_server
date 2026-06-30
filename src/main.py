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
from src.modules.chatbot.router import router as chatbot_router
from src.modules.special_offers import router as special_offers_router
from src.modules.special_offers.models import SpecialOffer
from src.modules.testimonials import router as testimonials_router
from src.modules.testimonials.models import Testimonial
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastAPIIntegration
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastAPIIntegration()],
            traces_sample_rate=1.0,
        )
        print("Sentry SDK error tracking initialized.")
    except Exception as e:
        print(f"Failed to initialize Sentry SDK: {e}")

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastAPIIntegration
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastAPIIntegration()],
            traces_sample_rate=1.0,
        )
        print("Sentry SDK error tracking initialized.")
    except Exception as e:
        print(f"Failed to initialize Sentry SDK: {e}")

from sqlalchemy import text

Base.metadata.create_all(bind=engine)

# Auto-migration: Ensure new Order workflow columns exist in PostgreSQL
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR DEFAULT 'pending' NOT NULL;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_status VARCHAR DEFAULT 'requested' NOT NULL;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_text VARCHAR;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_rating INTEGER;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_submitted_at TIMESTAMP WITH TIME ZONE;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS prepaid_method VARCHAR;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS prepaid_number VARCHAR;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS prepaid_txid VARCHAR;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS recipient_name VARCHAR;"))
        conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS recipient_email VARCHAR;"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS purchase_amount DOUBLE PRECISION DEFAULT 0.0;"))
        conn.execute(text("ALTER TABLE special_offers ADD COLUMN IF NOT EXISTS category_id INTEGER;"))
        conn.execute(text("ALTER TABLE special_offers ADD COLUMN IF NOT EXISTS product_id INTEGER;"))
        conn.commit()
    print("Database order columns auto-migration completed successfully.")
except Exception as e:
    print(f"Error executing database order columns auto-migration: {e}")

os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="MediStore API")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Dynamic CORS origins configuration
cors_origins_str = os.getenv("CORS_ALLOWED_ORIGINS")
if cors_origins_str:
    origins = [o.strip() for o in cors_origins_str.split(",")]
else:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://10.10.13.99:5173",
        "http://10.10.13.99:8010"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Security Response Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(accounts_router.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(categories_router.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(products_router.router, prefix="/api/v1/products", tags=["products"])
app.include_router(cart_router.router, prefix="/api/v1/cart", tags=["cart"])
app.include_router(orders_router.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(contact_router.router, prefix="/api/v1/contact", tags=["contact"])
app.include_router(special_offers_router.router, prefix="/api/v1/special-offers", tags=["special-offers"])
app.include_router(testimonials_router.router, prefix="/api/v1/testimonials", tags=["testimonials"])
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["chatbot"])

@app.get("/health")
def health_check():
    return {"status": "success", "message": "Server is healthy"}
