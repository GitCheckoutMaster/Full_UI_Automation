'''
Main agent module with rate limit handling and optimizations
'''

import os
import asyncio
import time
from dotenv import load_dotenv
from agents.file_mgmt_agent import file_management_agent

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App
from google.genai.errors import ClientError

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
        "Your name is JARVIS. You are an advanced AI assistant specialized in automating tasks on Windows systems. "
        "You are intelligent, methodical, and provide clear explanations of what you're doing. "
        
        "\nCORE CAPABILITIES:"
        "\n- File management: reading, listing, searching, and editing files and directories"
        "\n- Web search: finding information about system paths, configurations, and how-to guides"
        "\n- Task orchestration: coordinating multiple agents to accomplish complex workflows"
        
        "\nWHEN YOU RECEIVE A TASK:"
        "\n1. ANALYZE USER INTENT: Understand exactly what the user is asking for"
        "\n2. GATHER INFORMATION: If you need system-specific details (paths, locations, configurations):"
        "     - Search the web or use your knowledge to find default Windows paths"
        "     - For example: Default Downloads folder is C:\\Users\\[username]\\Downloads"
        "     - Construct the correct path using provided information"
        "\n3. PLAN YOUR APPROACH: Break down the task into steps"
        "     - Identify which agents you need (file_management_agent for file operations)"
        "     - Plan the sequence of operations"
        "\n4. EXECUTE: Call the appropriate agents with clear instructions"
        "     - Provide complete context to agents"
        "     - Include specific paths and requirements"
        "\n5. SYNTHESIZE RESULTS: Collect responses from agents and present them to the user"
        "     - Organize information clearly"
        "     - Highlight key findings (files found, content retrieved, etc.)"
        "     - Explain what was searched and what was found"
        
        "\nAVAILABLE AGENTS:"
        "\n- file_management_agent: Handles all file operations (read, write, list, search)"
        
        "\nBEST PRACTICES:"
        "\n- When listing directories, always check subdirectories if requested"
        "\n- When searching for files, report all subdirectories explored"
        "\n- Provide file content exactly as retrieved, with no modifications"
        "\n- If an operation fails, the file_management_agent will retry with different approaches"
        "\n- Always inform the user of what you found, what you searched, and any errors encountered"
        "\n- Be conversational and clear in your final response to the user"
    ),
    tools=[
        AgentTool(agent=file_management_agent),
    ],
)

app = App(name="jarvis_app", root_agent=main_agent)
session_service = InMemorySessionService()
jarvis_runner = Runner(session_service=session_service, app=app)

# Track API calls for rate limiting
class RateLimitTracker:
    def __init__(self, max_requests=15, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times = []
    
    def can_make_request(self):
        """Check if we can make a request without hitting rate limit"""
        now = time.time()
        # Remove old requests outside the window
        self.request_times = [t for t in self.request_times if now - t < self.window_seconds]
        return len(self.request_times) < self.max_requests
    
    def record_request(self):
        """Record that we made a request"""
        self.request_times.append(time.time())
    
    def get_wait_time(self):
        """Calculate how long to wait before next request is allowed"""
        if not self.request_times:
            return 0
        oldest_request = min(self.request_times)
        wait_time = (oldest_request + self.window_seconds) - time.time()
        return max(0, wait_time)

rate_limiter = RateLimitTracker()

async def run_with_rate_limit_handling():
    """Run the agent with proper rate limit handling"""
    
    session_id = "session_002"
    user_id = "user_jaymi"
    
    await session_service.create_session(session_id=session_id, user_id=user_id, app_name="jarvis_app")
    
    user_message = Content(
        role="user",
        parts=[Part(text="my profile name is 'jaymi' so give me the list of text files in my downloads folder (use default downloads folder path in windows) (check sub folders too) and if the downloads folder have any test.txt file print the content of that file as well")],
    )
    
    print("\n" + "="*50)
    print("JARVIS CONVERSATION")
    print("="*50 + "\n")
    
    # Check rate limit before starting
    if not rate_limiter.can_make_request():
        wait_time = rate_limiter.get_wait_time()
        print(f"⚠️ Rate limit active. Please wait {wait_time:.1f} seconds before trying again.")
        print(f"💡 Free tier limit: 15 requests per minute")
        return
    
    rate_limiter.record_request()
    
    events = []
    all_text_responses = []
    
    try:
        async for event in jarvis_runner.run_async(
            new_message=user_message,
            session_id=session_id,
            user_id=user_id
        ):
            events.append(event)
            
            # Collect ALL text parts from all model responses
            if event.content and event.content.parts:
                print(f"[DEBUG] Processing model response with {len(event.content.parts)} parts.")
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        all_text_responses.append(part.text)
                        print(f"[DEBUG] Captured text: {part.text[:100]}...")
                    elif hasattr(part, 'function_call'):
                        print(f"[TOOL CALL] {part.function_call}")
    
    except ClientError as e:
        error_str = str(e)
        
        # Handle rate limit errors
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print("\n❌ RATE LIMIT ERROR (429)")
            print("="*50)
            print("\n🔴 You've hit Google's free tier rate limit!")
            print("📊 Free tier allows: 15 API requests per minute")
            print("\n💡 SOLUTIONS:")
            print("   1. WAIT: Come back in 1-2 minutes and try again")
            print("   2. UPGRADE: Get a paid API key for higher limits")
            print("      → Go to https://ai.google.dev")
            print("      → Enable billing")
            print("      → Rate limit increases to 1500+ requests/minute")
            print("   3. OPTIMIZE: Reduce the number of nested agents")
            print("\n⏱️  Current time: Next request available in ~65 seconds")
        else:
            print(f"\n❌ ERROR: {error_str}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"An error occurred during the agent run: {e}")
        import traceback
        traceback.print_exc()
    
    # Print the final response
    print("\n" + "="*50)
    if all_text_responses:
        print("JARVIS RESPONSE:")
        print("="*50 + "\n")
        for i, response in enumerate(all_text_responses, 1):
            if i > 1:
                print("\n" + "-"*50 + "\n")
            print(response)
    else:
        print("No response generated")
        print("="*50 + "\n")
        if events:
            print("Debug - All events and their parts:")
            for i, event in enumerate(events):
                print(f"\nEvent {i}:")
                print(f"  Author: {event.author}")
                print(f"  Role: {event.content.role if event.content else 'None'}")
                if event.content and event.content.parts:
                    for j, part in enumerate(event.content.parts):
                        part_type = type(part).__name__
                        print(f"  Part {j}: {part_type}")
                        if hasattr(part, 'text'):
                            print(f"    Text: {part.text[:150] if part.text else 'None'}...")
                        if hasattr(part, 'tool_call'):
                            print(f"    Tool call: {part.tool_call}")
                else:
                    print(f"  No parts in this event")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_with_rate_limit_handling())