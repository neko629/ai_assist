SEARCH_TOOL = {
    "name": "search",
    "description": "使用谷歌搜索从互联网中获取实时信息，以回答用户的问题。",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "通过搜索从互联网获取信息的问题,关键词或短语"
            }
        },
        "required": ["query"]
    }
}

TOOL_DEFINITIONS = {
    "search": SEARCH_TOOL
}