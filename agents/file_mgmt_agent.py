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

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

def exit_loop(tool_context: ToolContext) -> dict:
    tool_context.actions.escalate = True
    return {}

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

starter_file_management_agent = Agent(
    name="starter_file_management_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "You are a file management agent that reads and writes files. "
        "When asked to read a file, use the read_file tool and return ONLY the file content. "
        "Do not analyze or interpret the content - just return it exactly as it is. "
        "Your response should be in this format: 'File content: [actual content here]'"
        "When you are asked to list items in a directory, use the list_items tool and return ONLY the list of files. "
    ),
    tools=[file_management_toolset],
    output_key="response",
)

checker_agent = Agent(
    name="checker_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "Check if 'response' indicates success. "
        "If the file operation was successful, reply exactly 'SUCCESS'. "
        "If not, reply exactly 'FAILURE: <error message>'."
    ),
    output_key="checker_response",
)

retry_agent = Agent(
    name="retry_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "If 'checker_response' is 'FAILURE: <error message>', retry the file operation by using the file_management_toolset again and also use different approches to attempt to fix the error after analyzing the error message."
        "If 'checker_response' is 'SUCCESS', do not take any action except  **you MUST call the 'exit_loop' function and print out a proper response and output if the query required any** "
    ),
    output_key="response",
    tools=[FunctionTool(exit_loop), file_management_toolset],
)

loop_agent = LoopAgent(
    name="loop_agent",
    sub_agents=[checker_agent, retry_agent],
    max_iterations=10,
)

file_management_agent = SequentialAgent(
    name="file_mgmt_agent",
    sub_agents=[starter_file_management_agent, loop_agent],
)


if __name__ == "__main__":
    async def main():
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.adk.apps.app import App
        from google.genai.types import Content, Part
        
        app = App(name="test_app", root_agent=file_management_agent)
        session_service = InMemorySessionService()
        runner = Runner(session_service=session_service, app=app)
        
        session_id = "test_session_001"
        user_id = "test_user"
        
        await session_service.create_session(session_id=session_id, user_id=user_id, app_name="test_app")
        
        user_message = Content(
            role="user",
            parts=[Part(text="in C:\\Users\\jaymi\\Downloads there is a file named test.txt read the content of that file (maybe its inside some of the folders in there look inside there too and if you do print out the names of that subdirectories that you looked inside) After you find the file, append \"Devanshu\" in it" )],
        )
        
        async for event in runner.run_async(
            new_message=user_message,
            session_id=session_id,
            user_id=user_id
        ):
            if event.content and event.content.role == 'model' and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print("Result:", part.text)
    
    asyncio.run(main())
