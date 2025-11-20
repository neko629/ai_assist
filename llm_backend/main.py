from starlette.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.logger import get_logger, log_structured
from fastapi import FastAPI
from app.core.middleware import LoggingMiddleware


logger = get_logger(service = "main")

app = FastAPI(title = "AI Assist REST API")

app.add_middleware(LoggingMiddleware)

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True, # 允许携带凭证
    allow_methods=["*"],   # 允许所有方法
    allow_headers=["*"],   # 允许所有头信息
)

app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}