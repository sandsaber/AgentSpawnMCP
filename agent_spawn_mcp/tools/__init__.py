from .chat import register_chat_tools
from .vision import register_vision_tools
from .files import register_file_tools
from .search import register_search_tools
from .agent import register_agent_tools
from .info import register_info_tools

def register_all_tools(mcp):
    register_info_tools(mcp)
    register_chat_tools(mcp)
    register_vision_tools(mcp)
    register_file_tools(mcp)
    register_search_tools(mcp)
    register_agent_tools(mcp)

__all__ = ["register_all_tools"]
