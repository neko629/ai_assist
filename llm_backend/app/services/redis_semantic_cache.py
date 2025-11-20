
from typing import Optional, List, Dict
import redis
import asyncio
import aiohttp
import hashlib
import json
from app.core import math_utils
from app.core.logger import get_logger
from app.core.config import settings
from datetime import datetime

logger = get_logger(service="redis_cache")

class RedisSemanticCache:
    def __init__(
            self,
            redis_url: str = None,
            model_name: str = None,
            score_threshold: float = None,
            prefix: str = "ai-assist",
            user_id: Optional[int] = None,  # 添加用户ID
            max_cache_size: int = 1000,  # 每个用户最大缓存条数
            cleanup_interval: int = 3600  # 清理间隔(秒)
    ):
        self.redis = redis.from_url(redis_url or settings.REDIS_URL)
        self.model_name = model_name or settings.OLLAMA_EMBEDDING_MODEL
        self.score_threshold = score_threshold or settings.REDIS_CACHE_THRESHOLD
        self.prefix = f"{prefix}:{user_id}" if user_id else prefix
        self.max_cache_size = max_cache_size
        self.cleanup_interval = cleanup_interval

        # 启动自动清理任务
        asyncio.create_tash(self._auto_cleanup())

    async def _get_ollama_embedding(self, text: str) -> List[float]: #  获取文本向量
        # 使用 Ollama 生成文本向量
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.OLLAMA_BASE_URL}/api/embed",
                    json = {
                        "model": self.model_name,
                        "input": text  # 使用 input 而不是 prompt, 符合 Ollama API 规范
                    }
                ) as response:
                    result = await response.json()
                    return result["embeddings"][0]  # 返回第一个向量
        except Exception as e:
            logger.error(f"Error getting Ollama embedding: {str(e)}", exc_info=True) #exc_info=True 用于打印堆栈信息
            raise

    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本向量"""
        try:
            # 直接使用 ollama 的 embedding 接口
            embedding = await self._get_ollama_embedding(text)
            if not embedding: # 如果没有获取到向量
                raise ValueError("Failed to get embedding")
            return embedding
        except Exception as e:
            logger.error(f"Error in get_embedding: {str(e)}", exc_info=True)
            raise

    def _get_vector_key(self, message: str) -> str:
        """生成 Redis 键"""
        message_hash = hashlib.md5(message.encode()).hexdigest()
        return f"{self.prefix}:{message_hash}"

    def _get_response_key(self, message: str) -> str:
        """生成响应存储的键名"""
        message_hash = hashlib.md5(message.encode()).hexdigest()
        return f"{self.prefix}:response:{message_hash}"

    def _get_metadata_key(self, message: str) -> str:
        """生成元数据存储的键名"""
        message_hash = hashlib.md5(message.encode()).hexdigest()
        return f"{self.prefix}:metadata:{message_hash}"

    def _get_last_user_message(self, messages: List[dict]) -> str:
        """获取用户的最后一条消息内容"""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    async def _auto_cleanup(self):
        """自动清理过期缓存"""
        while True: # 不停循环
            try:
                # 获取所有缓存键
                pattern = f"{self.prefix}:metadata:*"
                all_keys = [key.decode("utf-8") for key in self.redis.keys(pattern)]

                if len(all_keys) > self.max_cache_size:
                    cache_items = []
                    for key in all_keys:
                        metadata = json.loads(self.redis.get(key.encode("utf-8")).decode("utf-8")) # 编码再解码, 确保正确处理
                        cache_items.append((key, metadata.get("last_access", 0))) # 获取最后访问时间

                    # 按访问时间排序
                    cache_items.sort(key=lambda x: x[1])

                    # 删除最旧的条目直到达到限制
                    items_to_remove = len(all_keys) - self.max_cache_size
                    for key, _ in cache_items[:items_to_remove]:
                        hash_id = key.split(":")[-1]
                        await self._remove_cache_item(hash_id)
                logger.info(f"Cache cleanup completed for prefix {self.prefix}")
            except Exception as e:
                logger.error(f"Error during cache cleanup: {str(e)}", exc_info=True)
            await asyncio.sleep(self.cleanup_interval)  # 等待下一个清理周期


    async def _remove_cache_item(self, hash_id: str):
        """删除一个缓存项的所有相关键"""
        try:
            # 所有key都需要编码
            self.redis.delete(
                f"{self.prefix}:vec:{hash_id}".encode('utf-8'),
                f"{self.prefix}:resp:{hash_id}".encode('utf-8'),
                f"{self.prefix}:meta:{hash_id}".encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error removing cache item: {str(e)}", exc_info=True)

    async def _update_metadata(self, message: str):
        """更新缓存元数据的访问时间"""
        try:
            meta_key = self._get_metadata_key(message)
            current_meta = self.redis.get(meta_key)
            if current_meta:
                current_meta = json.loads(current_meta.decode("utf-8"))
            else:
                current_meta = {"access_count": 0}

            metadata = {
                "last_access": datetime.now().timestamp(),
                "access_count": current_meta["access_count"] + 1
            }
            self.redis.set(meta_key, json.dumps(metadata), ex=settings.REDIS_CACHE_EXPIRE)
        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}", exc_info=True)

    async def lookup(self, messages: List[dict]) -> Optional[str]:
        """查找缓存的响应"""
        try:
            user_message = self._get_last_user_message(messages)
            if not user_message:
                return None

            current_vector = await self.getembedding(user_message)

            # 遍历所有缓存项，计算相似度
            pattern = f"{self.prefix}:vec:*"
            all_vectors = [key.decode('utf-8') for key in self.redis.keys(pattern)]
            max_similarity = 0 # 最大相似度
            most_similar_key = None # 最相似的键

            for vec_key in all_vectors:
                cached_vector = json.loads(self.redis.get(vec_key.encode("utf-8")).decode("utf-8"))
                similarity = math_utils.cosine_similarity(current_vector, cached_vector)
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_key = vec_key
            if max_similarity >= self.score_threshold and most_similar_key:
                hash_id = most_similar_key.split(":")[-1]
                resp_key = self._get_response_key(user_message)
                cached_response = self.redis.get(resp_key.encode("utf-8"))

                if cached_response:
                    await self._update_metadata(user_message)
                    logger.info(f"Cache hit with similarity {max_similarity:.4f}")
                    return cached_response.decode("utf-8")
            return None
        except Exception as e:
            logger.error(f"Error in lookup: {str(e)}", exc_info=True)
            return None


    async def update(self, messages: List[Dict], response: str, expire: int = None):
        try:
            user_message = self._get_last_user_message(messages)
            if not user_message:
                return

            vector = await self._get_embedding(user_message)

            vec_key = self._get_vector_key(user_message)
            resp_key = self._get_response_key(user_message)
            meta_key = self._get_metadata_key(user_message)

            expire = expire or settings.REDIS_CACHE_EXPIRE

            self.redis.set(vec_key.encode('utf-8'), json.dumps(vector), ex=expire)
            self.redis.set(resp_key.encode('utf-8'), response.encode('utf-8'), ex=expire)

            metadata = {
                "created_at": datetime.now().timestamp(), # 创建时间
                "last_access": datetime.now().timestamp(), # 最后访问时间
                "access_count": 1 # 访问次数
            }
            self.redis.set(meta_key.encode('utf-8'), json.dumps(metadata), ex=expire)
            logger.info(f"Cache update for message: {user_message[:10]}...")
        except Exception as e:
            logger.error(f"Error in update: {str(e)}", exc_info=True)
