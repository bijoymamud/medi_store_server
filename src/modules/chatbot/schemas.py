from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ChatbotMessageRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None


class ChatbotMessageResponse(BaseModel):
    reply: str
    history: List[Dict[str, Any]]

