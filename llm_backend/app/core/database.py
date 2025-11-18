import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 设置 SQLAlchemy 日志级别为 INFO，以显示 SQL 查询日志, 便于调试
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# 创建异步引擎
engine= create_async_engine(
    settings.DATABASE_URL,
    echo = True,   # 设置为 False 也可以关闭 SQL 日志
    pool_pre_ping = True, # 自动检测断开的连接
    pool_size = 5,  # 连接池大小， 保持 5 个连接处于可用状态。在高并发情况下，最多可以同时处理 5 个数据库请求，而不需要每次都去创建新的连接。
    max_overflow = 10  # 最大连接数
)

# 创建异步会话工厂, 用于生成数据库会话
AsyncSessionLocal = sessionmaker(
    bind = engine, # 绑定引擎
    class_ = AsyncSession, # 使用异步会话类
    expire_on_commit = False # 提交后不失效数据, 即可继续使用
)

# 创建基类, 所谓基类就是所有模型类的父类
Base = declarative_base()

# 获取数据库会话的依赖函数, 用于 FastAPI 的依赖注入
async def get_db():
    async with AsyncSessionLocal() as session: # 生成数据库会话, async with 表示这是一个异步上下文管理器, 会自动处理会话的打开和关闭
        try:
            yield session # 生成数据库会话
            await session.commit() # 提交事务
        except Exception:
            await session.rollback() # 回滚事务
            raise # 抛出异常
        finally:
            await session.close()  # 关闭会话, await 关键字表示这是一个异步操作