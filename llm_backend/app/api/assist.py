from http.client import HTTPException

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from app.core.logger import get_logger, log_structured
from app.services.llm_factory import LLMFactory
from fastapi.responses import StreamingResponse

logger = get_logger(service="assist-api")

router = APIRouter()

class ReasonRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: int

class ChatMessage(BaseModel):
    messages: List[Dict[str, str]]
    user_id: int
    conversation_id: int

@router.post("/chat")
async def chat_endpoint(request: ChatMessage):
    try:
        logger.info(f"Received chat request from user {request.user_id} for conversation {request.conversation_id}")
        chat_service = LLMFactory.create_chat_service()
        # TODO: 会话处理
        return StreamingResponse(
            chat_service.generate_stream(
                messages = request.messages,
                user_id = request.user_id,
                conversation_id = request.conversation_id
            ),
            media_type = "text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return HTTPException(status_code = 500, detail = str(e))

@router.post("/reason")
async def reason_endpoint(request: ReasonRequest):
    try:
        logger.info(f"Processing reasoning request for user {request.user_id}")
        reasoner = LLMFactory.create_reasoner_service()

        log_structured(
            "reason_request",
            {
                "user_id": request.user_id,
                "message_count": len(request.messages),
                "last_message": request.messages[-1]["content"][:100] + "..."
            }
        )

        return StreamingResponse(
            reasoner.generate_stream(request.messages),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Reasoning error for user {request.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

