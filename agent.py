'''
Main agent module which will orchestrates all other agents and tools to perform the desired automation task.
'''

import os
import asyncio
from dotenv import load_dotenv
from application_mgmt_agent import software_mgmt_agent
from file_mgmt_agent import file_management_agent

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

main_agent = Agent(
    name="jarvis",
    model="gemini-2.5-flash-lite",
    instruction=(
        "Your name is jarvis. You are an advanced AI assistant and a friendly chatbot. "
        "You must always be helpful and respectful towards humans. "
        "You have access to file_management_agent which can read and write files. "
        "\n\nIMPORTANT WORKFLOW:"
        "\n1. When asked to read and analyze a file, first call file_management_agent to read it."
        "\n2. After receiving the file content from file_management_agent, YOU must analyze it yourself."
        "\n3. Always provide your analysis in a clear, conversational response."
        "\n4. NEVER just pass through the tool's response - always add your own analysis and insights."
    ),
    tools=[AgentTool(agent=file_management_agent)],
)

if __name__ == "__main__":
    app = App(name="jarvis_app", root_agent=main_agent)
    session_service = InMemorySessionService()
    runner = Runner(session_service=session_service, app=app)

    async def main():
        session_id = "session_001"
        user_id = "user_jaymi"
        
        await session_service.create_session(session_id=session_id, user_id=user_id, app_name="jarvis_app")
        
        user_message = Content(
            role="user",
            parts=[Part(text="can you list all video files in my downloads folders ( C:\\Users\\jaymi\\Downloads )?")],
        )
        
        print("\n" + "="*50)
        print("JARVIS CONVERSATION")
        print("="*50 + "\n")
        
        events = []
        last_model_text = None
        
        async for event in runner.run_async(
            new_message=user_message,
            session_id=session_id,
            user_id=user_id
        ):
            events.append(event)
            
            # Capture the last model response with text
            if event.content and event.content.role == 'model':
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        last_model_text = part.text
        
        # Print the final response
        if last_model_text:
            print("JARVIS:")
            print(last_model_text)
        else:
            print("No response generated")
            print("\nDebug - All events:")
            for i, event in enumerate(events):
                print(f"\n Event {i}:")
                print(f"  Author: {event.author}")
                print(f"  Role: {event.content.role if event.content else 'None'}")
                if event.content and event.content.parts:
                    for j, part in enumerate(event.content.parts):
                        part_type = type(part).__name__
                        print(f"  Part {j}: {part_type}")
                        if hasattr(part, 'text'):
                            print(f"    Text: {part.text[:100] if part.text else 'None'}...")
        
        print("\n" + "="*50 + "\n")

    asyncio.run(main())