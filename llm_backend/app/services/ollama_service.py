from app.core.logger import get_logger
from app.core.config import settings
from typing import List, Dict, Optional, Callable, AsyncGenerator
import aiohttp
import json

logger = get_logger(service="ollama")

class OllamaService:
    def __init__(self):
        logger.info("OllamaService initialized")
        self.base_url = settings.OLLAMA_BASE_URL
        self.chat_model = settings.OLLAMA_CHAT_MODEL
        self.reason_model = settings.OLLAMA_REASON_MODEL

    async def generate_stream(
            self,
            messages: List[Dict],
            user_id: Optional[int] = None,
            conversation_id: Optional[int] = None,
            on_complete: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        # 生成流式回复
        try:
            model = self.reason_model
            logger.info(f"Using model: {model}")

            full_response = [] # 存储完整回复
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json = {
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "keep_alive": -1,
                        "options": {
                            "temperature": 0.7,
                        }
                    }
                ) as response:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if content := chunk.get("message", {}).get("content"):
                                    full_response.append(content)
                                    content = json.dumps(content, ensure_ascii=False) # ensure_ascii=False 处理中文
                                    yield f"data: {content}\n\n" # 返回流式数据
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error: {str(e)}")
                                continue
            # 调用回调函数
            if on_complete:
                complete_response = "".join(full_response) # 拼接完整回复, 不直接用 full_response 避免列表格式
                await on_complete(user_id, conversation_id, messages, complete_response)

        except Exception as e:
            logger.error(f"Error in generate_stream: {str(e)}", exc_info=True)
            error_msg = json.dumps(f"生成回复时出错: {str(e)}", ensure_ascii=False)
            yield f"data: {error_msg}\n\n"
            raise

    async def generate(self, message: List[Dict]) -> str:
        # 非流式生成回复
        try:
            model = self.chat_model
            logger.info(f"Using model: {model}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json = {
                        "model": model,
                        "messages": message,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                        }
                    }
                ) as response:
                    result = await response.json()
                    return result["message"]["content"]
        except Exception as e:
            logger.error(f"Error in generate: {str(e)}", exc_info=True)
            raise







