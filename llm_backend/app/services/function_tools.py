from dataclasses import dataclass
from typing import Callable, Dict, List, Any
import json

@dataclass
class FunctionTool:
    name: str
    description: str
    parameters: Dict
    handler: Callable

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, FunctionTool] = {}

    def register(self, tool: FunctionTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> FunctionTool:
        return self._tools.get(name)

    def get_tools_definition(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self._tools.values()
        ]

    async def execute_tool(self, name: str, arguments: str) -> Any:
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")

        args = json.loads(arguments)
        return await tool.handler(**args)