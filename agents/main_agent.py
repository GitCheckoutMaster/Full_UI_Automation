'''
Main agent module which will orchestrates all other agents and tools to perform the desired automation task.
'''

import os
import asyncio
from dotenv import load_dotenv
from file_mgmt_agent import file_management_agent

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App
from google.adk.tools import google_search

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    print("GOOGLE_API_KEY found and set: ", api_key[:4] + "..." )
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    raise EnvironmentError("GOOGLE_API_KEY not found in .env file or environment.")

main_agent = Agent(
    name="jarvis",
    model="gemini-2.5-flash-lite",
    instruction=(
        "Your name is jarvis. You are an advanced AI assistant capable of automating tasks. "
        "You have access to multiple specialized agents and a web search function. "
        
        "\nWhen you encounter something you don't know:"
        "\n- Search the web to find the answer"
        "\n- Examples: default paths, app installation locations, how to do something"
        "\n- Use this knowledge to inform the agents you call"
        
        "\nAVAILABLE AGENTS:"
        "\n- file_management_agent"
        
        "\nWORKFLOW:"
        "\n1. Understand user intent"
        "\n2. Search if you need info (paths, how-tos, etc.)"
        "\n3. Route to appropriate agents"
        "\n4. Provide analysis and results to the user in a clear, conversational manner"
    ),
    tools=[
        AgentTool(agent=file_management_agent),
    ],
)

app = App(name="jarvis_app", root_agent=main_agent)
session_service = InMemorySessionService()
jarvis_runner = Runner(session_service=session_service, app=app)


if __name__ == "__main__":

    async def main():
        session_id = "session_002"
        user_id = "user_jaymi"
        
        await session_service.create_session(session_id=session_id, user_id=user_id, app_name="jarvis_app")
        
        user_message = Content(
            role="user",
            parts=[Part(text="my profile name is 'jaymi' so give me the list of text files in my downloads folder (use default downloads folder path in windows) and if the downloads folder have any test.txt file print the content of that file as well" )],
        )
        
        print("\n" + "="*50)
        print("JARVIS CONVERSATION")
        print("="*50 + "\n")
        
        events = []
        last_model_text = None
        
        try:
            async for event in jarvis_runner.run_async(
                new_message=user_message,
                session_id=session_id,
                user_id=user_id
            ):
                events.append(event)
                
                # Capture the last model response with text
                if event.content and event.content.role == 'model' and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            last_model_text = part.text
                            print(f"[DEBUG] Captured text: {last_model_text[:100]}")
        except Exception as e:
            print(f"An error occurred during the agent run: {e}")
            import traceback
            traceback.print_exc()
        
        # Print the final response
        if last_model_text:
            print("\nJARVIS:")
            print(last_model_text)
        else:
            print("No response generated")
            print("\nDebug - All events:")
            for i, event in enumerate(events):
                print(f"\nEvent {i}:")
                print(f"  Author: {event.author}")
                print(f"  Role: {event.content.role if event.content else 'None'}")
                if event.content and event.content.parts:
                    for j, part in enumerate(event.content.parts):
                        part_type = type(part).__name__
                        print(f"  Part {j}: {part_type}")
                        if hasattr(part, 'text'):
                            print(f"    Text: {part.text[:100] if part.text else 'None'}...")
                        if hasattr(part, 'tool_call'):
                            print(f"    Tool call: {part.tool_call}")
        
        print("\n" + "="*50 + "\n")

    asyncio.run(main())