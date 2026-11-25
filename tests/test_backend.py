import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_db
from backend.models import User, Conversation, Message, Memory, UserPreference
from backend.config import settings

# Force fast built-in engine during automated testing to avoid external network dependencies
settings.AI_BACKEND = "builtin"

# Use StaticPool in-memory SQLite so all connections share the same database tables in tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# Test Data
TEST_USER = {
    "full_name": "Antigravity Tester",
    "email": "testuser@dakshu.ai",
    "password": "Password123!"
}

# --- 1. Health Check Test ---
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "healthy" in data["database"]
    assert "version" in data
    assert "ai_backend" in data

# --- 2. Registration & Auth Tests ---
def test_user_registration(client):
    response = client.post("/api/auth/register", json=TEST_USER)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == TEST_USER["email"]
    assert data["user"]["full_name"] == TEST_USER["full_name"]

def test_duplicate_registration_fails(client):
    response = client.post("/api/auth/register", json=TEST_USER)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()

def test_user_login_success(client):
    response = client.post("/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == TEST_USER["email"]

def test_user_login_invalid_password(client):
    response = client.post("/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": "WrongPassword999!"
    })
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()

def test_user_logout(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()

# --- 3. Profile & User Preferences Tests ---
def get_auth_headers(client):
    login_res = client.post("/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_user_profile_and_preferences(client):
    headers = get_auth_headers(client)

    # Get Profile
    get_res = client.get("/api/profile", headers=headers)
    assert get_res.status_code == 200
    profile = get_res.json()
    assert profile["email"] == TEST_USER["email"]
    assert profile["preferences"] is not None

    # Update Preferences
    pref_res = client.put(
        "/api/memories/preferences",
        headers=headers,
        json={
            "preferred_language": "tamil",
            "response_style": "motivational",
            "voice_enabled": True
        }
    )
    assert pref_res.status_code == 200
    updated_pref = pref_res.json()
    assert updated_pref["preferred_language"] == "tamil"
    assert updated_pref["response_style"] == "motivational"

# --- 4. Personal Memory Management Tests ---
def test_personal_memory_crud(client):
    headers = get_auth_headers(client)

    # 1. Create Memory
    add_res = client.post(
        "/api/memories",
        headers=headers,
        json={"memory_text": "I am studying Machine Learning and building Dakshu AI"}
    )
    assert add_res.status_code == 201
    memory = add_res.json()
    memory_id = memory["id"]
    assert memory["memory_text"] == "I am studying Machine Learning and building Dakshu AI"

    # 2. List Memories
    list_res = client.get("/api/memories", headers=headers)
    assert list_res.status_code == 200
    memories = list_res.json()
    assert len(memories) >= 1
    assert any(m["id"] == memory_id for m in memories)

    # 3. Delete Memory
    del_res = client.delete(f"/api/memories/{memory_id}", headers=headers)
    assert del_res.status_code == 200

    # 4. Verify Deleted
    list_res2 = client.get("/api/memories", headers=headers)
    assert not any(m["id"] == memory_id for m in list_res2.json())

# --- 5. Conversations CRUD Tests ---
def test_conversations_crud(client):
    headers = get_auth_headers(client)

    # Create Conversation
    create_res = client.post(
        "/api/conversations",
        headers=headers,
        json={"title": "Test AI Study Thread"}
    )
    assert create_res.status_code == 201
    conv = create_res.json()
    conv_id = conv["id"]
    assert conv["title"] == "Test AI Study Thread"

    # List Conversations
    list_res = client.get("/api/conversations", headers=headers)
    assert list_res.status_code == 200
    assert any(c["id"] == conv_id for c in list_res.json())

    # Get Details
    detail_res = client.get(f"/api/conversations/{conv_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == conv_id

    # Delete Conversation
    del_res = client.delete(f"/api/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 200

# --- 6. AI Chat & Specialized Modules Tests ---
def test_chat_endpoint_companion(client):
    headers = get_auth_headers(client)
    chat_res = client.post(
        "/api/chat",
        headers=headers,
        json={
            "message": "Hello Dakshu! Can you introduce yourself?",
            "module": "companion"
        }
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "content" in data
    assert len(data["content"]) > 10
    assert data["role"] == "assistant"
    assert data["conversation_id"] > 0

def test_chat_multilingual_tamil_tanglish(client):
    headers = get_auth_headers(client)
    chat_res = client.post(
        "/api/chat",
        headers=headers,
        json={
            "message": "Vanakkam Dakshu! Enna panlaam innaiku?",
            "module": "companion"
        }
    )
    assert chat_res.status_code == 200
    content = chat_res.json()["content"]
    assert "vanakkam" in content.lower() or "dakshu" in content.lower()

def test_chat_study_buddy_module(client):
    headers = get_auth_headers(client)
    chat_res = client.post(
        "/api/chat",
        headers=headers,
        json={
            "message": "Explain how Python lists work and give me a quick quiz",
            "module": "study"
        }
    )
    assert chat_res.status_code == 200
    content = chat_res.json()["content"]
    assert "quiz" in content.lower() or "python" in content.lower()

def test_chat_english_partner_module(client):
    headers = get_auth_headers(client)
    chat_res = client.post(
        "/api/chat",
        headers=headers,
        json={
            "message": "I want to improve my English fluency for interviews.",
            "module": "english"
        }
    )
    assert chat_res.status_code == 200
    content = chat_res.json()["content"]
    assert "english" in content.lower() or "practice" in content.lower()

# --- 7. Streaming SSE Endpoint Test ---
def test_chat_stream_endpoint(client):
    headers = get_auth_headers(client)
    with client.stream(
        "POST",
        "/api/chat/stream",
        headers=headers,
        json={
            "message": "Dakshu, what are 3 daily productivity tips?",
            "module": "motivation"
        }
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        chunks = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                chunks.append(line)
        assert len(chunks) > 0

def test_chat_location_tracking(client):
    headers = get_auth_headers(client)
    chat_res = client.post(
        "/api/chat",
        headers=headers,
        json={
            "message": "Where am I located right now?",
            "module": "companion",
            "client_timezone": "Asia/Kolkata",
            "client_location": "Chennai, Tamil Nadu, India"
        }
    )
    assert chat_res.status_code == 200
    content = chat_res.json()["content"]
    assert "chennai" in content.lower() or "location" in content.lower()

# --- 8. Security & Authorization Protection Test ---
def test_unauthorized_access_denied(client):
    # Clear any residual session cookies to test unauthenticated request
    client.cookies.clear()

    # Missing Auth token should fail with 401
    res = client.get("/api/conversations")
    assert res.status_code == 401

    res_mem = client.get("/api/memories")
    assert res_mem.status_code == 401

    res_profile = client.get("/api/profile")
    assert res_profile.status_code == 401
