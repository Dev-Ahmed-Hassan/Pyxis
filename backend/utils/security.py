import os
from datetime import UTC, datetime, timedelta

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    expires_at = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expires_at},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("Token subject is missing")
        return user_id
    except JWTError as error:
        raise ValueError("Invalid or expired access token") from error
