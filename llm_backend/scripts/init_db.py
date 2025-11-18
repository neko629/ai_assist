import sys
from pathlib import Path

# 添加项目根目录到 PYTHONPATH, 作用是为了让脚本能够找到 app 模块
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

import asyncio # 导入 asyncio 模块, 用于处理异步操作
from app.core.database import Base, engine
from app.models import user
from app.core.logger import get_logger

logger = get_logger(service="init_db") # 获取日志记录器

async def init_db(): # 定义异步函数 init_db 用于初始化数据库
    try:
        logger.info("Initializing database...")
        async with engine.begin() as conn:
            # 删除所有表（如果存在）
            await conn.run_sync(Base.metadata.drop_all)
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        # 在事件循环关闭前显式释放引擎/连接池，避免析构时调度到已关闭的 loop
        try:
            await engine.dispose()
        except Exception:
            pass

def main():
    try:
        asyncio.run(init_db())
    except RuntimeError as e:
        logger.error(f"Runtime error: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
if __name__ == "__main__":
    main()




