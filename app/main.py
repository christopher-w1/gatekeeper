from fastapi import FastAPI, HTTPException
from datetime import datetime, timezone
from models import *
from app.user_repository import UserRepository
from rate_limiter import RateLimiter
from utils import hash_password, verify_password, is_valid_password, is_valid_email, is_valid_username
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
import uuid
import tomllib

# --- Load Config ---
with open("config.toml", "rb") as f:
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
active_sessions = {}

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
        session_token=str(uuid.uuid4()),
    )
    await repo.save(user)
    return {"status": "success", "message": "User registered"}

@app.post("/get-user-data", response_model=UserDataResponse)
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

    return UserDataResponse(**user.dict())

@app.post("/login-user")
async def login_user(data: LoginRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    user = await repo.get_user_by_email(data.email)
    if not user or not verify_password(user.hashed_password, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.session_token = str(uuid.uuid4())
    user.last_access = datetime.now(timezone.utc)
    await repo.update(user)
    return {"status": "success", "session_token": user.session_token}

@app.post("/logout-user")
async def logout_user(data: LogoutRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    user = await repo.get_user_by_session_token(data.session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session token")

    user.session_token = ""
    await repo.update(user)
    return {"status": "success", "message": "Logged out"}

@app.post("/modify-user")
async def modify_user(data: ModifyUserRequest):
    if data.api_token not in valid_tokens and require_api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    user = await repo.get_user_by_session_token(data.session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session token")

    if data.username:
        user.username = data.username
    if data.email:
        user.email = data.email
    if data.password:
        user.hashed_password = hash_password(data.password)
    if data.is_active is not None:
        user.is_active = data.is_active

    await repo.update(user)
    return {"status": "success", "message": "User modified"}
