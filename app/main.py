from fastapi import FastAPI, HTTPException
from datetime import datetime, timezone
from models import *
from user_repository import UserRepository
from rate_limiter import RateLimiter
from utils import hash_password, verify_password, is_valid_password, is_valid_email, is_valid_username
from sqlalchemy.ext.asyncio import create_async_engine
from session_manager import SessionManager
import uuid
import tomllib

# --- Load Config ---
with open("./app/config.toml", "rb") as f:
    config = tomllib.load(f)

db_url = config["database"]["url"]
echo_db = config["database"].get("echo", False)
valid_tokens = config["auth"]["valid_tokens"]
require_api_token = config["auth"]["require_api_token"]
rate_limit_conf = config["ratelimit"]

# --- Setup ---
app = FastAPI()
engine = create_async_engine(db_url, echo=echo_db)
repo = UserRepository(engine)
login_rate_limiter = RateLimiter(
    max_attempts=rate_limit_conf["max_attempts"],
    window_seconds=rate_limit_conf["window_seconds"]
)
session = SessionManager(timeout=1800)

# --- Endpoints ---
@app.post("/register-user")
async def register_user(data: RegisterRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    if not is_valid_email(data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    existing = await repo.get_user_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if not is_valid_username(data.username):
        raise HTTPException(status_code=400, detail="Invalid username format")
    if not is_valid_password(data.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 7 characters long and include one uppercase letter, one lowercase letter, and one digit"
        )
    hashed_pw = hash_password(data.password)
    user = UserModel(
        username=data.username,
        email=data.email,
        hashed_password=hashed_pw,
    )
    await repo.save(user)
    return {"status": "success", "message": "User registered"}

@app.post("/get-user-data")
async def get_user_data(data: GetUserDataRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    if not any([data.email, data.username, data.id]):
        raise HTTPException(status_code=400, detail="At least one of email, username, or id is required.")

    user = None
    if data.email:
        user = await repo.get_user_by_email(data.email)
    elif data.username:
        user = await repo.get_user_by_username(data.username)
    elif data.id:
        user = await repo.get_user_by_id(data.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_is_active = any(session.is_session_active(token) for token in session.tokens_by_id.get(user.id, []))
    user_data = {
        "username": user.username,
        "email": user.email,
        "registered_at": user.registered_at,
        "last_access": user.last_access,
        "is_active": user_is_active,
    }

    return {"status": "success", "user_data": user_data}

@app.post("/login-user")
async def login_user(data: LoginRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    if not login_rate_limiter.allow_attempt(data.email):
        raise HTTPException(status_code=429, detail="Too many login attempts")

    user = await repo.get_user_by_email(data.email)
    if not user or not verify_password(user.hashed_password, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = str(uuid.uuid4())
    session.create_session(token, user.id)

    user.last_access = datetime.now(timezone.utc)
    await repo.update(user)
    return {"status": "success", "session_token": token, "user_id": user.id, "message": "Logged in"}

@app.post("/logout-user")
async def logout_user(data: LogoutRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")

    if not session.is_session_active(data.session_token):
        raise HTTPException(status_code=401, detail="Invalid session token")

    session.close_session_for_token(data.session_token)
    return {"status": "success", "message": "Logged out"}

@app.post("/modify-user")
async def modify_user(data: ModifyUserRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")

    if not session.is_session_active(data.session_token):
        raise HTTPException(status_code=401, detail="Invalid session token")

    user_id = session.tokens[data.session_token]["user_id"]
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.username:
        if not is_valid_username(data.username):
            raise HTTPException(status_code=400, detail="Invalid username format")
        if data.username != user.username:
            if await repo.get_user_by_username(data.username):
                raise HTTPException(status_code=400, detail="Username already taken")
        user.username = data.username

    user.username = data.username
        
    if data.email:
        if not is_valid_email(data.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        if data.email != user.email:
            if await repo.get_user_by_email(data.email):
                raise HTTPException(status_code=400, detail="Email already registered")
        user.email = data.email
    if data.password:
        if not is_valid_password(data.password):
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 7 characters long and include one uppercase letter, one lowercase letter, and one digit"
            )
        user.hashed_password = hash_password(data.password)

    await repo.update(user)
    return {"status": "success", "message": "User modified"}


if __name__ == "__main__":
    import uvicorn
    host = config["server"].get("host", "127.0.0.1")
    port = config["server"].get("port", 8000)
    uvicorn.run("main:app", host=host, port=port, reload=False)