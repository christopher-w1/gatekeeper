import httpx
import pytest

# Define the base URL for the FastAPI app
BASE_URL = "http://localhost:8000"  # Change this if needed

# Test data
test_user = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "Test@1234",
    "api_token": "your_api_token_here",  # Replace with a valid token if required
}

# Function to test user registration
async def test_register_user():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/register-user", json=test_user)
        print(f"Response: {response.text}")  # Debugging line to see the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "User registered"

# Function to test user login
async def test_login_user():
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"],
        "api_token": test_user["api_token"],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/login-user", json=login_data)
        print(f"Response: {response.text}")  # Debugging line to see the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "session_token" in data
        assert "user_id" in data

        # Store the session token for future requests
        return data["session_token"], data["user_id"]

# Function to test retrieving user data
async def test_get_user_data(session_token, user_id):
    get_data = {
        "api_token": test_user["api_token"],
        "id": user_id,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/get-user-data", json=get_data)
        print(f"Response: {response.text}")  # Debugging line to see the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user_data"]["username"] == test_user["username"]
        assert data["user_data"]["email"] == test_user["email"]

# Test runner function
async def run_tests():
    # Test registration
    await test_register_user()

    # Test login
    session_token, user_id = await test_login_user()

    # Test get user data
    await test_get_user_data(session_token, user_id)

# Run the tests using pytest async
if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tests())
