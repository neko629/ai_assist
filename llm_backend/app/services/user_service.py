from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.hashing import get_password_hash, verify_password
from datetime import datetime
from typing import Optional
from app.core.logger import get_logger

logger = get_logger(service = "user_service")

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        # check if username or email exist
        query = select(User).where(
            or_(
                User.username == user_data.username,
                User.email == user_data.email,
            )
        )
        result = await self.db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == user_data.username:
                logger.warning(f"Register failed! User with username {user_data.username} already exists")
                raise ValueError("该用户名已被使用")
            if existing_user.email == user_data.email:
                logger.warning(f"Register failed! User with email {user_data.email} already exists")
                raise ValueError("该邮箱已被使用")

        # 创建新用户
        new_user = User(
            username = user_data.username,
            email = user_data.email,
            password_hash = get_password_hash(user_data.password)
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        query = select(User).where(
            User.email == email
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Authenticate failed! User with email {email} does not exist")
            return None

        verify_result = verify_password(password, user.password_hash)

        if not verify_result:
            logger.warning(f"Authenticate failed! Password error")
            return None

        user.last_login = datetime.utcnow()
        await self.db.commit()

        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        query = select(User).where(
            User.id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(
            User.email == email
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()