import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool, exit_loop
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# def exit_loop(tool_context: ToolContext) -> dict:
#     """Exit the loop agent when operation is successful"""
#     tool_context.actions.escalate = True
#     return {"status": "exit", "message": "Operation completed successfully. Exiting loop."}

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
        "You are a file management agent responsible for reading files, listing directories, and editing files. "
        "Execute the requested file operation using the available tools. "
        "\n"
        "READING FILES: Use the read_file tool with the exact file path. Return the file content exactly as retrieved. "
        "FORMAT: 'File content:\n[exact file content]' "
        "\n"
        "LISTING DIRECTORIES: Use the list_items tool to show all files and folders in a directory. "
        "FORMAT: 'Directory contents:\n[list of items]' "
        "\n"
        "EDITING/APPENDING FILES: Use the edit_file tool to modify or append content to files. "
        "FORMAT: 'File updated successfully. Path: [path], Content appended: [what was added]' "
        "\n"
        "SEARCHING IN SUBDIRECTORIES: If a file is not found in the initial directory, use list_items to explore subdirectories. "
        "Track which subdirectories you've searched and report them. "
        "\n"
        "ERROR HANDLING: If an operation fails, clearly state the error and the path/file you were trying to access. "
        "Do not attempt to fix errors yourself - let the retry_agent handle recovery. "
        "\n"
        "CRITICAL: Always return raw content without interpretation or summarization."
    ),
    tools=[file_management_toolset],
    output_key="response",
)

checker_agent = Agent(
    name="checker_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "You are a validation agent. Analyze the 'response' field to determine if the file operation succeeded or failed. "
        "\n"
        "SUCCESS CRITERIA: "
        "- File was read and content is displayed "
        "- Directory was listed successfully "
        "- File was edited/appended successfully "
        "- Operation completed without errors "
        "\n"
        "FAILURE CRITERIA: "
        "- File not found "
        "- Path does not exist "
        "- Permission denied "
        "- Invalid path format "
        "- Any error message is present "
        "\n"
        "RESPOND WITH EXACTLY ONE OF: "
        "'SUCCESS' - if the operation completed without errors "
        "'FAILURE: [specific error description]' - if there was an error. Include the exact error message and the path that failed. "
        "\n"
        "Be precise and concise in your response."
    ),
    output_key="checker_response",
)

retry_agent = Agent(
    name="retry_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "You are a recovery and completion agent. Check the 'checker_response' field. "
        "\n"
        "IF SUCCESS ('SUCCESS'): "
        "1. Call the **exit_loop** function to terminate the loop "
        "2. Provide a comprehensive final response that includes: "
        "   - What operation was performed "
        "   - The result (file content, list of items, or confirmation of edit) "
        "   - Any subdirectories that were searched (if applicable) "
        "   - Success confirmation "
        "\n"
        "IF FAILURE ('FAILURE: [error]'): "
        "1. Analyze the error message and previous attempts "
        "2. Determine the root cause (file location, path format, permission issue, etc.) "
        "3. Attempt alternative approaches: "
        "   - Try different path formats or variations "
        "   - Search in parent/sibling directories if file not found "
        "   - Explore subdirectories using list_items "
        "   - Check for file in subdirectories using list_items "
        "   - Verify directory structure before attempting operations "
        "4. Use the file_management_toolset to retry with corrected approach "
        # "5. Report what you tried, why it failed, and what you're trying next "
        "5. Do not respond ANYTHING while retrying - just perform the operation "
        "\n"
        "ALWAYS be explicit about recovery attempts and reasoning."
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
            parts=[Part(text="(my windows profile name is 'jaymi') find test.txt and print its content in downloads folder (check subdirectories)" )],
        )
        
        async for event in runner.run_async(
            new_message=user_message,
            session_id=session_id,
            user_id=user_id
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print("Result from file_mgmt_agent: ", part.text)
                    elif hasattr(part, 'function_call'):
                        print("Function Call from file_mgmt_agent: ", part.function_call)
    
    asyncio.run(main())