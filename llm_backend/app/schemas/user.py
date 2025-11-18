from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel): # 基础用户模型
    username: str
    email: EmailStr

class UserCreate(UserBase): # 创建用户模型，继承自 UserBase
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase): # 响应用户模型，继承自 UserBase
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None # 可选字段
    status: str

    class Config:
        from_attributes = True # 允许从 ORM 模型实例创建 Pydantic 模型实例

class Token(BaseModel): # 令牌模型
    access_token: str
    token_type: str = "bearer"