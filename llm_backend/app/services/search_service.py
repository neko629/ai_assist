import asyncio
from typing import List, Dict, Optional, Callable, AsyncGenerator
from app.core.logger import get_logger
from app.prompts.search_prompts import SEARCH_SYSTEM_PROMPT, SEARCH_SUMMARY_PROMPT
from app.services.function_tools import ToolRegistry, FunctionTool
from app.tools.definitions import SEARCH_TOOL
from app.tools.search import SearchTool
from openai import AsyncOpenAI
from app.core.config import settings
import datetime
import json

logger = get_logger(service="search")


class SearchService:
    def __init__(self):
        logger.info("Search Service Initiated")
        self.client = AsyncOpenAI(
            api_key =  "ollama",
            base_url = "http://localhost:11434/v1/"
        )
        self.model = "qwen2.5:7b"
        self.search_tool = SearchTool()

        # 初始化工具注册中心
        self.tool_registry = ToolRegistry()

        # 注册搜索工具
        self.tool_registry.register(
            FunctionTool(
                **SEARCH_TOOL,
                handler=self._handle_search
            )
        )

        # 生成工具描述
        self.tools_description = self.generate_tools_description()

    def generate_tools_description(self) -> str:
        tool_description = []

        for tool_def in self.tool_registry.get_tools_definition():
            func = tool_def.get("function")
            name = func["name"]
            desc = func["description"]
            params = []

            # 获取必须参数和描述
            for param_name, param_info in func["parameters"]["properties"].items():
                if param_name in func["parameters"].get("required", []):
                    params.append(f"{param_name}, 作用是: {param_info['description']}")

            tool_desc = (
                f"{name},{desc}"
                f", 必须参数有: " if params else ""
                                                 f"{', '.join(params)}"
            )
            tool_description.append(tool_desc)
        return "当前可用的工具有: " + " ; ".join(tool_description)

    async def _handle_search(self, query: str) -> List[Dict]:
        return await asyncio.to_thread(  # 将同步方法放到线程池中执行
            self.search_tool.search, query
        )

    async def _call_with_tool(self, query: str) -> Dict:
        # 调用模型并获取工具调用结果
        try:
            logger.info(f"Call model with query: {query}")

            response = await self.client.chat.completions.create(
                model = self.model,
                messages = query,
                tools = self.tool_registry.get_tools_definition(),
                tool_choice = "auto"
                # 自动选择工具, 其他选项: "none", "always", "manual", 表示不使用工具,"总是使用工具", "手动选择"
            )

            logger.info(f"Model response: {response.choices[0]}")
            return response.choices[0]
        except Exception as e:
            logger.error(f"Error in _call_with_tool: {str(e)}", exc_info=True)
            raise

    async def generate(
            self,
            query: str,
            user_id: Optional[int] = None,
            conversation_id: Optional[int] = None,
            on_complete: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Starting search generation for query: {query}")

            messages = [
                {
                    "role": "system",
                    "content": SEARCH_SYSTEM_PROMPT.format(
                        tools_description=self.tools_description
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ]

            choice = await self._call_with_tool(messages)
            logger.info(f"Tool call response: {choice}")

            # 根据 finish_reason 处理不同情况
            finish_reason = choice.finish_reason
            if finish_reason == "tool_call":  # 需要调用工具
                tool_calls = choice.message.tool_calls
                if tool_calls:
                    tool_call = tool_calls[0]
                    logger.info(f"Processing tool call: {tool_call}")

                    try:
                        # 执行工具调用
                        search_results = await self.tool_registry.execute_tool(
                            tool_call.function.name,
                            tool_call.function.arguments
                        )
                        logger.info(f"Got {len(search_results)} search results")

                        if search_results:
                            # 构建上下文内容
                            context = []
                            for result in search_results:
                                context.append(
                                    f"来源: {result['title']}\n"
                                    f"链接: {result['url']}\n"
                                    f"内容: {result['snippet']}\n"
                                )

                            # 构建带上下文的提示
                            context_prompt = SEARCH_SUMMARY_PROMPT.format(
                                context="\n---\n".join(context),
                                query=query,
                                cur_data=datetime.now().strftime("%Y-%m-%d")
                            )

                            # 告诉前端是搜索结果
                            yield f"data: {json.dumps({'type': 'search_start'}, ensure_ascii=False)}\n\n"

                            search_data = {
                                "type": "search_results",
                                "total": len(search_results),
                                "query": json.loads(tool_call.function.arguments)[
                                    "query"],
                                "results": [
                                    {
                                        "title": result["title"],
                                        "url": result["url"],
                                        "snippet": result["snippet"]
                                    }
                                    for result in search_results
                                ]
                            }

                            yield f"data: {json.dumps(search_data, ensure_ascii=False)}\n\n"

                            logger.info(f"final message to model: {context_prompt}")
                            # 使用上下文重新调用模型生成最终回答
                            async for chunk in await self.client.chat.completions.create(
                                    model=self.model,
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": context_prompt
                                        }
                                    ],
                                    stream=True
                            ):
                                if chunk.choices[0].delta.content:
                                    content = json.dumps(chunk.choices[0].delta.content,
                                                         ensure_ascii=False)
                                    yield f"data: {content}\n\n"

                    except Exception as e:
                        pass
            elif choice.finish_reason == "stop":  # 正常完成
                logger.info(f"Stopping search generation for query: {query}")
                # 告诉前端是正常回答
                yield f"data: {json.dumps({'type': 'normal_start'}, ensure_ascii = False)}\n\n"
                # 使用流式 API 重新生成回答
                stream_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True
                )

                full_response = []
                async for chunk in stream_response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response.append(content)
                        yield f"data: {json.dumps({'type': 'direct_content', 'content': content}, ensure_ascii = False)}\n\n"

                # 如果有回调函数，调用它
                if on_complete and user_id is not None and conversation_id is not None:
                    complete_response = "".join(full_response)
                    await on_complete(user_id, conversation_id, [{"role": "user", "content": query}], complete_response)



        except Exception as e:
            logger.error(f"Error in generate: {str(e)}", exc_info=True)
            raise
