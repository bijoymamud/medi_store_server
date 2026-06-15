import jwt
from datetime import datetime, timedelta, timezone
import os

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENV") == "production":
        raise RuntimeError("SECRET_KEY environment variable must be set in production!")
    SECRET_KEY = "supersecretkey"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # 30 minutes

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token if decoded_token["exp"] >= datetime.now(timezone.utc).timestamp() else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None
