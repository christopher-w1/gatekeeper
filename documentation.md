Overview:
---------
This API handles user registration, authentication, data retrieval, session management, and user modification. It uses token-based security, rate limiting for login, and an SQLite database with asynchronous SQLModel and SQLAlchemy.

Configuration:
-------------
Loaded from `./app/config.toml`:
- Database URL: `config["database"]["url"]`
- API Token Requirement: `config["auth"]["require_api_token"]`
- Valid API Tokens: `config["auth"]["valid_tokens"]`
- Rate Limit Settings: `config["ratelimit"]`
- Session Timeout: 30 minutes (hardcoded)

Endpoints:
---------

1. `POST /register-user`
   - Registers a new user.
   
   Request Body (RegisterRequest):
   - api_token: str (required if enforced by config)
   - username: str
   - email: str
   - password: str
   
   Validations:
   - Email, username, and password must follow specific format rules.
   - Email and username must not be already registered.

   Response:
   {
     "status": "success",
     "message": "User registered"
   }

2. `POST /login-user`
   - Authenticates a user and creates a session.
   
   Request Body (LoginRequest):
   - api_token: str (required if enforced by config)
   - email: str
   - password: str
   
   Rate Limiting:
   - Based on email, prevents too many login attempts in a short window.
   
   Response:
   {
     "status": "success",
     "session_token": "<uuid>",
     "user_id": "<uuid>",
     "message": "Logged in"
   }

3. `POST /logout-user`
   - Terminates a session.
   
   Request Body (LogoutRequest):
   - api_token: str (required if enforced by config)
   - session_token: str
   
   Response:
   {
     "status": "success",
     "message": "Logged out"
   }

4. `POST /get-user-data`
   - Retrieves basic user data by email, username, or ID.
   
   Request Body (GetUserDataRequest):
   - api_token: str (required if enforced by config)
   - One of:
     - email: str
     - username: str
     - id: UUID
   
   Response:
   {
     "status": "success",
     "user_data": {
       "username": "...",
       "email": "...",
       "registered_at": "...",
       "last_access": "...",
       "is_active": true/false
     }
   }

5. `POST /modify-user`
   - Updates username, email, and/or password of the currently logged-in user.
   
   Request Body (ModifyUserRequest):
   - api_token: str (required if enforced by config)
   - session_token: str (must be valid and active)
   - Optional:
     - username: str
     - email: str
     - password: str
   
   Validations:
   - Email/username format & uniqueness
   - Password strength
   
   Response:
   {
     "status": "success",
     "message": "User modified"
   }

Notes:
------
- All endpoints require a valid `api_token` if `require_api_token = true` in config.
- Passwords are hashed with salt.
- Sessions are stored in memory and expire after 30 minutes of inactivity.
- Email and username validation is handled via `utils.py`.
