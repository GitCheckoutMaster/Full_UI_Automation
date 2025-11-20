import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

file_management_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="node",
            args=[
                "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\Root Server\\File_mgmt_server\\server.js"
            ],
        )
    )
)

file_management_agent = Agent(
    name="file_management_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "You are a file management agent that reads and writes files. "
        "When asked to read a file, use the read_file tool and return ONLY the file content. "
        "Do not analyze or interpret the content - just return it exactly as it is. "
        "Your response should be in this format: 'File content: [actual content here]'"
        "When you are asked to list items in a directory, use the list_items tool and return ONLY the list of files. "
    ),
    tools=[file_management_toolset],
)