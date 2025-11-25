import json
import os
from dotenv import load_dotenv

from openai import OpenAI


class Chatbot:
    def __init__(self, model: str, base_url: str, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    # 定义外部工具
    def get_weather(self, location: str) -> str:
        # 模拟获取天气信息
        weather_data = {
            "New York": "Sunny, 25°C",
            "San Francisco": "Foggy, 15°C",
            "London": "Rainy, 10°C",
            "Beijing": "Cloudy, 20°C",
            "Tokyo": "Windy, 18°C"
        }
        return weather_data.get(location, "Weather data not available")

    # 创建工具的 JsonSchema 描述
    def create_tools(self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city to get the weather for"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        return tools

    # 对话主函数
    def chat(self, user_message: str) -> str:
        # 添加系统角色消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant that can provide weather information."},
            {"role": "user", "content": user_message}
        ]

        print("Sending messages to OpenAI API:", messages)

        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            tools = self.create_tools()
        )

        # 检查 finish_reason
        finish_reason = response.choices[0].finish_reason

        if finish_reason == 'stop':
            print("Finish reason: stop, output:", response.choices[0].message.content)

        elif finish_reason == 'tool_calls':
            assistant_message = response.choices[0].message # 获取 assistant 消息
            print("Finish reason: tool_calls, assistant message:", assistant_message)

            messages.append(assistant_message) # 将 assistant 消息添加到对话中

            # 处理工具调用
            tool_calls = response.choices[0].message.tool_calls
            print("Tool calls:", tool_calls)
            if tool_calls:
                # 获取函数名称和参数
                function_name = tool_calls[0].function.name
                function_args = json.loads(tool_calls[0].function.arguments)

                # 定义可用的函数
                available_functions = {
                    "get_weather": self.get_weather,
                }

                # 动态调用相应的函数
                if function_name in available_functions:
                    function_response = available_functions[function_name](**function_args)
                    print(f"Function '{function_name}, args: {function_args}' response:", function_response)

                    # 添加函数响应到消息中
                    messages.append({
                        "role": "tool",
                        "content": str(function_response),
                        "tool_call_id": tool_calls[0].id, # 关联工具调用 ID
                    })

                    print(f"final messages before final API call:", messages)

                    final_response = self.client.chat.completions.create(
                        model = self.model,
                        messages = messages,
                    )

                    print(f"final response from OpenAI API:", final_response)
                else:
                    print(f"Function '{function_name}' not found among available functions.")
            else:
                print("No tool calls found in the assistant message.")
        else:
            print(f"Unhandled finish reason: {finish_reason}")


load_dotenv()
api_key = str(os.getenv("DEEPSEEK_API_KEY"))
base_url = str(os.getenv("DEEPSEEK_BASE_URL"))
model_name = str(os.getenv("DEEPSEEK_MODEL"))

use_ollama = True
if use_ollama:
    api_key = "ollama"
    base_url = "http://localhost:11434/v1/"
    model_name = "qwen2.5:7b"

user_message = "What's the weather like in Hangzhou today?"
chatbot = Chatbot(model_name, base_url, api_key)
chatbot.chat(user_message)




