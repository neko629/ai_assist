
from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, func

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key = True, index = True)
    conversation_id = Column(Integer, nullable = False)
    sender = Column(String(64), nullable = False)
    content = Column(Text, nullable = False)
    created_at = Column(DateTime, server_default = func.now())
    message_type = Column(String(32), default = "text")