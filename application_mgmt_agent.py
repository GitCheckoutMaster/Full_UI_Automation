import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# TODO: Agent is not exitting the loop on success, fix that.
# TODO: Add this file to github repo.

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


def exit_loop(tool_context: ToolContext) -> dict:
    tool_context.actions.escalate = True
    return {}


automation_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="node",
            args=[
                "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\automation_mcp_server\\server.js"
            ],
        )
    )
)

starter_agent = Agent(
    name="starter_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "You are an automation starter agent. "
        "Your task is to use the open_software tool from automation_toolset to open software. "
        'You must call the tool with JSON: {"name": "software name"}'
    ),
    tools=[automation_toolset],
    output_key="response",
)

checker_agent = Agent(
    name="checker_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "Check if 'response' indicates success. "
        "If software opened successfully, reply exactly 'SUCCESS'. "
        "If not, reply exactly 'FAILURE: <error message>'."
    ),
    output_key="checker_response",
)

retry_agent = Agent(
    name="retry_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "If checker_response is SUCCESS, **you MUST call the 'exit_loop' function and do nothing else.** "
        "If checker_response starts with FAILURE, extract a better possible name and "
        "retry using the open_software tool again. "
        'You must always call open_software tool using JSON: {"name": "corrected name"}'
    ),
    tools=[automation_toolset, FunctionTool(exit_loop)],
    output_key="response",
)

loop_agent = LoopAgent(
    name="automation_loop_agent",
    sub_agents=[checker_agent, retry_agent],
    max_iterations=5,
)

software_mgmt_agent = SequentialAgent(
    name="software_mgmt_agent",
    sub_agents=[starter_agent, loop_agent],
)

# runner = InMemoryRunner(agent=software_mgmt_agent)


# async def main():
#     print("\n===== PROCESS STARTED in software_mgmt_agent =====\n")
#     response = await runner.run_debug("i want to make a note in notepad")
#     print("\n===== FINAL RESULT in software_mgmt_agent =====")
#     print(response)


# asyncio.run(main())
