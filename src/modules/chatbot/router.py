from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.modules.chatbot.schemas import ChatbotMessageRequest, ChatbotMessageResponse
from src.utils.rate_limit import RateLimiter


router = APIRouter()
chatbot_limiter = RateLimiter(limit=20, window=60)


def run_chatbot_reply(message: str, db: Session, history):
    from src.modules.chatbot.chat import get_bot_reply

    return get_bot_reply(message, db, history)


@router.post("/message", response_model=ChatbotMessageResponse, dependencies=[Depends(chatbot_limiter)])
def message(payload: ChatbotMessageRequest, db: Session = Depends(get_db)):
    return run_chatbot_reply(payload.message, db, payload.history)
