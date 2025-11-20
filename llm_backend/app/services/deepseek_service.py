import asyncio
import json
import time
from app.core.logger import get_logger
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.redis_semantic_cache import RedisSemanticCache
from typing import AsyncGenerator, List, Dict, Optional, Callable

logger = get_logger(service="deepseek_service")

class DeepseekService:
    def __init__(self, model: str = "deepseek-chat"):
        logger.info("DeepseekService initialized with model: %s", model)
        self.client = AsyncOpenAI(
            api_key = settings.DEEPSEEK_API_KEY,
            base_url = settings.DEEPSEEK_BASE_URL
        )
        self.model = model
        self.cache = RedisSemanticCache(prefix="deepseek_cache")

    async def _stream_cached_response(self, response: str, delay: float = 0.05)-> AsyncGenerator[str, None]:
        """模拟流式返回缓存的响应"""
        # 每次返回 4 个字符
        chunks = [response[i : i+4] for i in range(0, len(response), 4)]
        for chunk in chunks:
            await asyncio.sleep(delay) # 每次返回前等待 delay 秒
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    async def generate_stream(
            self,
            messages: List[Dict],
            user_id: Optional[int] = None,
            conversation_id: Optional[int] = None,
            on_complete: Optional[Callable[[int, int, List[Dict], str], None]] = None
    ) -> AsyncGenerator[str, None]:
       try:
            # 为每个用户创建独立的缓存实例, 以支持多用户缓存隔离
            cache = RedisSemanticCache(prefix = "deepseek_cache", user_id = user_id)
            start_time = time.time()
            # 检查缓存
            cached_response = await cache.lookup(messages)
            if cached_response: # 缓存命中
                response_time = time.time() - start_time
                logger.info(f"Cache hit! Response time: {response_time:.4f} seconds")

                async for chunk in self._stream_cached_response(cached_response):
                    yield chunk

                if on_complete and user_id is not None and conversation_id is not None:
                    await on_complete(user_id, conversation_id, messages, cached_response)
                return
            # 缓存未命中，调用 Deepseek API
            full_response = []
            response = await self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                stream = True
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = json.dumps(chunk.choices[0].delta.content, ensure_ascii=False)
                    full_response.append(content)
                    yield f"data: {content}\n\n"

            complete_response = "".join(full_response)
            # 将新响应存入缓存
            await cache.update(messages, complete_response)

            response_time = time.time() - start_time
            logger.info(f"Cache miss. Response time: {response_time:.4f} seconds")

            if on_complete and user_id is not None and conversation_id is not None:
                await on_complete(user_id, conversation_id, messages, complete_response)

       except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}", exc_info=True)
            error_msg = json.dumps(f"生成回复时出错: {str(e)}", ensure_ascii=False)
            yield f"data: {error_msg}\n\n"

    async def generate(self, messages: List[Dict]) -> str:
        """非流式生成回复"""
        try:
            response = await self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                stream = False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in generate: {str(e)}", exc_info=True)
            raise
