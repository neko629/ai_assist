from sqlalchemy import Column, Integer, String, DateTime, func, Enum
from app.core.database import Base
import enum

class DialogueType(enum.Enum):
    NORMAL = "普通对话"
    DEEP_THINKING = "深度思考"
    WEB_SEARCH = "联网检索"
    RAG = "RAG 问答"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    status = Column(String(32), default="ongoing")
    dialogue_type = Column(Enum(DialogueType), nullable=False)