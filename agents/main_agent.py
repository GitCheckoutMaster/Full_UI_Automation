"""
Main agent module with rate limit handling and optimizations
"""

import os
import asyncio
import time
from dotenv import load_dotenv
from file_mgmt_agent import file_management_agent
from vs_code_agent import vs_code_agent

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
    print("GOOGLE_API_KEY found and set: ", api_key[:4] + "...")
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    raise EnvironmentError("GOOGLE_API_KEY not found in .env file or environment.")

main_agent = Agent(
    name="jarvis",
    model="gemini-2.5-flash-lite",
    instruction="""
    Your name is JARVIS. You are a friendly, intelligent AI assistant specialized in automating tasks
    on Windows systems. You communicate clearly, politely, and helpfully. Your goal is to assist the
    user efficiently while keeping a professional yet approachable tone.

    =====================
    CORE CAPABILITIES
    =====================
    You have access to the following tools:

    1. File Management (via file_management_agent):
    - LIST FILES: List all files in a specified folder.
    - READ FILE: Print the contents of a specified file.
    - EDIT FILE: Modify or append content to a file safely.

    2. VS Code Automation (via vs_code_agent):
    - OPEN FOLDER: Open a folder in Visual Studio Code.
    - OPEN FILE: Open a file in VS Code; if the file does not exist, create it.
    - GET SETTINGS: Retrieve current VS Code user settings as a JSON object.

    =====================
    HOW TO HANDLE USER REQUESTS
    =====================
    1. GREET FRIENDLY: Always start interactions in a polite, approachable way.
    2. UNDERSTAND USER INTENT:
    - Identify what the user wants to do: file management or VS Code automation.
    - Determine necessary paths and filenames.
    3. PLAN AND EXECUTE:
    - For file management tasks, delegate to file_management_agent.
    - For VS Code tasks, delegate to vs_code_agent.
    - Always validate that paths exist or create files/folders as needed.
    4. RESPOND CLEARLY:
    - Explain what you did and confirm successful completion.
    - Example: "I have opened 'notes.txt' in VS Code. If the file didn't exist, it was created."
    5. ASK FOR CLARIFICATION:
    - If the user's request is ambiguous, politely ask for details before proceeding.
    6. SAFE BEHAVIOR:
    - Never perform destructive actions without explicit user confirmation.
    - Do not assume or fabricate paths or filenames; always work with valid Windows paths.

    =====================
    TONE AND STYLE
    =====================
    - Friendly, respectful, and helpful.
    - Clear and concise explanations.
    - Always confirm actions and results with the user.
    - Avoid technical jargon unless the user specifically requests it.
    """,
    tools=[
        AgentTool(agent=file_management_agent),
        AgentTool(agent=vs_code_agent),
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
        self.request_times = [
            t for t in self.request_times if now - t < self.window_seconds
        ]
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

    await session_service.create_session(
        session_id=session_id, user_id=user_id, app_name="jarvis_app"
    )

    user_message = Content(
        role="user",
        parts=[
            Part(
                text="list all video files in my Videos folder (profile name on windows is jaymi)"
            )
        ],
    )

    print("\n" + "=" * 50)
    print("JARVIS CONVERSATION")
    print("=" * 50 + "\n")

    # Check rate limit before starting
    if not rate_limiter.can_make_request():
        wait_time = rate_limiter.get_wait_time()
        print(
            f"Rate limit active. Please wait {wait_time:.1f} seconds before trying again."
        )
        print(f"Free tier limit: 15 requests per minute")
        return

    rate_limiter.record_request()

    events = []
    all_text_responses = []

    try:
        async for event in jarvis_runner.run_async(
            new_message=user_message, session_id=session_id, user_id=user_id
        ):
            events.append(event)

            # Collect ALL text parts from all model responses
            if event.content and event.content.parts:
                print(
                    f"[DEBUG] Processing model response with {len(event.content.parts)} parts."
                )
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        all_text_responses.append(part.text)
                        print(f"[DEBUG] Captured text: {part.text[:100]}...")
                    elif hasattr(part, "function_call"):
                        print(f"[TOOL CALL] {part.function_call}")

    except ClientError as e:
        error_str = str(e)

        # Handle rate limit errors
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print("\nRATE LIMIT ERROR (429)")
            print("=" * 50)
            print("\nYou've hit Google's free tier rate limit!")
            print("Free tier allows: 15 API requests per minute")
            print("\nSOLUTIONS:")
            print("   1. WAIT: Come back in 1-2 minutes and try again")
            print("   2. UPGRADE: Get a paid API key for higher limits")
            print("      → Go to https://ai.google.dev")
            print("      → Enable billing")
            print("      → Rate limit increases to 1500+ requests/minute")
            print("   3. OPTIMIZE: Reduce the number of nested agents")
            print("\nCurrent time: Next request available in ~65 seconds")
        else:
            print(f"\nERROR: {error_str}")
            import traceback

            traceback.print_exc()

    except Exception as e:
        print(f"An error occurred during the agent run: {e}")
        import traceback

        traceback.print_exc()

    # Print the final response
    print("\n" + "=" * 50)
    if all_text_responses:
        print("JARVIS RESPONSE:")
        print("=" * 50 + "\n")
        for i, response in enumerate(all_text_responses, 1):
            if i > 1:
                print("\n" + "-" * 50 + "\n")
            print(response)
    else:
        print("No response generated")
        print("=" * 50 + "\n")
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
                        if hasattr(part, "text"):
                            print(
                                f"    Text: {part.text[:150] if part.text else 'None'}..."
                            )
                        if hasattr(part, "tool_call"):
                            print(f"    Tool call: {part.tool_call}")
                else:
                    print(f"  No parts in this event")

    print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(run_with_rate_limit_handling())
