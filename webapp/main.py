from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import httpx
import tomllib

app = FastAPI()
templates = Jinja2Templates(directory="templates")

CONFIG_PATH = Path(__file__).parent.parent / "app" / "config.toml"
with open(CONFIG_PATH, "rb") as f:
    config = tomllib.load(f)

# Zugriff auf Gatekeeper-URL
host = config["server"]["host"]
port = config["server"]["port"]
gatekeeper_url = f"http://{host}:{port}"

@app.get("/", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, redirect: str = "/"):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "redirect": redirect
    })

@app.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    redirect: str = Form("/")
    ):
    async with httpx.AsyncClient() as client:
        api_response = await client.post(f"{gatekeeper_url}/login-user", json={
            "api_token": config["auth"]["valid_tokens"][0],
            "email": email,
            "password": password
        })
    if not redirect.startswith("/") or redirect.endswith("login"):
        redirect = "/welcome"
    if api_response.status_code == 200:
        response = RedirectResponse(url=redirect, status_code=302)
        response.set_cookie(key="session_token", value=api_response.json()["session_token"])
    else:
        response = templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Login failed",
            "redirect": redirect,
        })
    return response

@app.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("welcome.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    host = config["server"].get("host", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=80, reload=False)