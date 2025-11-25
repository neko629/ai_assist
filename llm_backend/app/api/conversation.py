from http.client import HTTPException

from fastapi import APIRouter
from pydantic import BaseModel
from app.core.logger import get_logger
from app.services.conversation_service import ConversationService

logger = get_logger(service="conversation")

router = APIRouter()

class CreateConversationRequest(BaseModel):
    user_id: int

class UpdateConversationNameRequest(BaseModel):
    name: str

@router.post("/conversations")
async def create_conversation(request: CreateConversationRequest):
    # 创建新会话
    try:
        conversation_id = await ConversationService.create_conversation(request.user_id)
        return {"conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/user/{user_id}")
async def get_user_conversations(user_id: int):
    # 获取用户的所有会话
    try:
        conversations = await ConversationService.get_user_conversations(user_id)
        return conversations
    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id}: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, user_id: int):
    # 获取会话的所有消息
    try:
        messages = await ConversationService.get_conversation_messages(conversation_id, user_id)
        return messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting messages for conversation {conversation_id}: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    # 删除会话及其所有消息
    try:
        await ConversationService.delete_conversation(conversation_id)
        return {"message": f"Conversation deleted: {conversation_id}"}
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@router.put("/conversations/{conversation_id}/name")
async def update_conversation_name(conversation_id: int, request: UpdateConversationNameRequest):
    # 更新会话名称
    try:
        await ConversationService.update_conversation_name(conversation_id, request.name)
        return {"message": f"Conversation name updated to: {request.name}"}
    except Exception as e:
        logger.error(f"Error updating conversation name for {conversation_id}: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))
