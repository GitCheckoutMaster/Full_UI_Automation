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

vs_code_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="node",
            args=[
                "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\Root Server\\VS_code_server\\server.js"
            ],
        )
    )
)

vs_code_starter_agent = Agent(
    name="vs_code_starter_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "You are a VS Code management agent responsible for opening files, editing code, and managing projects in Visual Studio Code. "
        "Execute the requested VS Code operation using the available tools. "

        "OPENING FILES: Use the open_file tool with the exact file path. Confirm the file is opened in VS Code. "
        "FORMAT: 'File opened successfully in VS Code. Path: [exact file path]' "

        "EDITING CODE: Use the edit_code tool to modify or append code in files. "
        "FORMAT: 'Code updated successfully. Path: [path], Changes made: [what was changed]' "

        "MANAGING PROJECTS: Use the manage_project tool to create, delete, or configure projects in VS Code. "
        "FORMAT: 'Project [action] successfully. Project name: [project name]' "

        "ERROR HANDLING: If an operation fails, clearly state the error and the path/file you were trying to access. "
        "Do not attempt to fix errors yourself - let the retry_agent handle recovery. "

        "CRITICAL: Always return raw content without interpretation or summarization."
    ),
    tools=[vs_code_toolset],
    output_key="response",
)

checker_agent = Agent(
    name="vs_code_checker_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "Input: [response]"
        "You are a VS Code operation checker agent. Your role is to verify the success of operations performed by the vs_code_starter_agent. "
        "After an operation is executed, analyze the response to determine if it was successful or if there were errors. "

        "SUCCESS CRITERIA: Look for confirmation phrases such as 'successfully' and ensure no error messages are present. "
        "If the operation was successful, respond with: 'SUCCESS' Only respond with this single word. "

        "ERROR DETECTION: If you detect any error messages or indications of failure, respond with: 'FAILURE: [error details]' Only respond with this format. "

        "YOUR RESPONSE SHOULD BE CONCISE AND TO THE POINT."
    ),
    output_key="verification",
)

vs_code_refiner_agent = Agent(
    name="vs_code_refiner_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=(
        "Input: [verification, response]"
        "You are a VS Code operation refiner agent. Your task is to improve the instructions for the vs_code_starter_agent based on feedback from the checker agent. "
        "If the [verification] output indicates a 'FAILURE: [error_details]', analyze the error details and refine the original instructions to address the issues. "

        "IMPROVEMENT STRATEGY: Identify what went wrong in the previous attempt and provide clearer, more detailed instructions to avoid similar errors. "
        "Focus on clarity, specificity, and completeness in your refinements. "

        "IF the [verification] output is 'SUCCESS', **call exit_loop** to end the refinement process. "
        "YOUR RESPONSE SHOULD BE THE REFINED INSTRUCTIONS ONLY, WITHOUT ANY ADDITIONAL COMMENTS."
    ),
    tools=[exit_loop],
    output_key="refined_instructions",
)

vs_code_loop_agent = LoopAgent(
    name="vs_code_loop_agent",
    sub_agents=[
        checker_agent,
        vs_code_refiner_agent,
    ],
)

vs_code_agent = SequentialAgent(
    name="vs_code_agent",
    sub_agents=[
        vs_code_starter_agent,
        vs_code_loop_agent,
    ],
)
