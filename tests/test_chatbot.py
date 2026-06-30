from fastapi.testclient import TestClient

from src.main import app
from src.modules.chatbot import router as chatbot_router


client = TestClient(app)


def test_chatbot_message_success(monkeypatch):
    def fake_run_chatbot_reply(message, db, history):
        return {
            "reply": f"Stub reply for: {message}",
            "history": [
                {"role": "user", "parts": [{"text": message}]},
                {"role": "model", "parts": [{"text": "Stub reply"}]},
            ],
        }

    monkeypatch.setattr(chatbot_router, "run_chatbot_reply", fake_run_chatbot_reply)

    payload = {
        "message": "Do you have blood pressure monitors?",
        "history": [{"role": "user", "parts": [{"text": "Hello"}]}],
    }

    response = client.post("/api/chatbot/message", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Stub reply for: Do you have blood pressure monitors?"
    assert len(data["history"]) == 2
    assert data["history"][0]["role"] == "user"
    assert data["history"][1]["role"] == "model"


def test_chatbot_message_validation():
    response = client.post("/api/chatbot/message", json={"history": []})

    assert response.status_code == 422
