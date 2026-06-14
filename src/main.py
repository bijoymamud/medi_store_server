from fastapi import FastAPI
from src.database.connection import engine, Base
from src.modules.users import router as users_router
from src.modules.auth import router as auth_router
from src.modules.accounts import router as accounts_router
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediStore API")

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

@app.get("/health")
def health_check():
    return {"status": "success", "message": "Server is healthy"}
