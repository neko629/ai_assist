from typing import List, Dict
import requests
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(service = "search_tool")

class SearchTool:
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        if not self.api_key:
            raise ValueError("SERPAPI_KEY is not set in settings.")

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        try:
            num_results = settings.SEARCH_RESULT_COUNT or num_results

            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "hl": "zh-CN",
                "gl": "cn"
            }

            response = requests.get(
                settings.SERPAPI_URL,
                params = params,
                timeout = settings.SERPAPI_TIMEOUT,
            )

            response.raise_for_status() # 检查请求是否成功, 否则抛出异常
            return self._parse_results(response.json())
        except Exception as e:
            logger.error(f"SearchTool error: {str(e)}", exc_info=True)
            return []

    def _parse_results(self, data: Dict) -> List[Dict]:
        results = []
        if "organic_results" in data:
            for item in data["organic_results"]:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                }
                results.append(result)
        return results[:settings.SEARCH_RESULT_COUNT]
