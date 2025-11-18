from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users" # 表名

    id = Column(Integer, primary_key=True, index=True)  # 主键，索引
    username = Column(String(50), unique=True, nullable=False)  # 用户名，唯一且不能为空
    email = Column(String(100), unique=True, nullable=False)  # 邮箱，唯一且不能为空
    password_hash = Column(String(255), nullable=False)  # 密码哈希，不能为空
    created_at = Column(DateTime, server_default=func.now(),nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)  # 最后登录时间，可以为空
    status = Column(String(16), nullable=False, default='active')  # 用户状态，默认为 'active'
