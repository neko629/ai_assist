from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.services.user_service import UserService
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger import get_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token") # 定义 OAuth2 密码模式的令牌 URL

logger = get_logger(service = "security")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy() # 复制数据以进行编码
    if expires_delta:
        expire = datetime.utcnow() + expires_delta # 计算过期时间
    else:
        # 如果没有提供 expires_delta，则 30 分钟后过期
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) # 将过期时间添加到要编码的数据
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) # 使用 SECRET_KEY 和指定的算法编码 JWT
    return encoded_jwt

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub") # 从 JWT 负载中提取用户的电子邮件, sub 是 subject 的缩写，表示令牌的主题，一般用来存储用户的唯一标识，比如用户ID或邮箱。
        if not email:
            logger.warning("No email provided")
            raise credentials_exception
    except JWTError: # 捕获 JWT 解码错误
        logger.warning("JWT decode error")
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email=email)
    if not user:
        logger.warning(f"User not found: {email}")
        raise credentials_exception
    return user
