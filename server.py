from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from agents.main_agent import jarvis_runner, session_service
from google.genai.types import Content, Part
import json

app = FastAPI(title="JARVIS UI Automation Agent")

origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_or_create_session(app_name, session_id, user_id):
    session = await session_service.get_session(session_id=session_id, user_id=user_id, app_name=app_name)
    if not session:
        return await session_service.create_session(session_id=session_id, user_id=user_id, app_name=app_name)
    return session

async def agent_response_generator(user_prompt: str, session_id: str, user_id: str):
    """
    Generator that streams agent responses to the client.
    Collects all text parts from the final model response.
    """
    user_message = Content(
        role="user",
        parts=[Part(text=user_prompt)],
    )
    
    await get_or_create_session("jarvis_app", session_id, user_id)
    
    try:
        # Collect all events from the agent run
        all_events = []
        final_text_parts = []
        
        async for event in jarvis_runner.run_async(
            new_message=user_message,
            session_id=session_id,
            user_id=user_id
        ):
            all_events.append(event)
            
            # Collect text parts from all model responses
            if event.content and event.content.role == "model" and event.content.parts:
                for part in event.content.parts:
                    # Check for text content
                    if hasattr(part, "text") and part.text:
                        final_text_parts.append(part.text)
        
        # Stream the collected responses
        if final_text_parts:
            # Yield each text part as it was collected
            for text in final_text_parts:
                yield f"{text}\n\n"
            yield "[DONE]\n\n"
        else:
            # If no text parts found, stream debug info
            yield f"Agent completed but returned no text. Event count: {len(all_events)}\n\n"
            yield "[DEBUG] Check server logs for full response structure.\n\n"
            yield "[DONE]\n\n"
            
            # Log debug info to server console
            print("\n[DEBUG] Response Analysis:")
            for i, event in enumerate(all_events):
                print(f"\nEvent {i}:")
                print(f"  Author: {event.author}")
                if event.content:
                    print(f"  Role: {event.content.role}")
                    if event.content.parts:
                        for j, part in enumerate(event.content.parts):
                            part_type = type(part).__name__
                            print(f"  Part {j}: {part_type}")
                            if hasattr(part, "text"):
                                print(f"    Text: {part.text[:100] if part.text else 'None'}...")
                            if hasattr(part, "tool_call"):
                                print(f"    Tool call: {part.tool_call}")
    
    except Exception as e:
        print(f"\n[ERROR] Exception during agent run: {str(e)}")
        # import traceback
        # traceback.print_exc()
        yield f"Error during agent run: {str(e)}\n\n"
        yield "[DONE]\n\n"


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    API endpoint for chat requests.
    Receives user prompt and streams agent response back.
    """
    try:
        data = await request.json()
        user_prompt = data.get("prompt")
    except json.JSONDecodeError:
        return StreamingResponse(
            iter(["data: Error: Invalid JSON in request\n\n", "data: [DONE]\n\n"]),
            media_type="text/event-stream"
        )
    
    if not user_prompt or user_prompt.strip() == "":
        return StreamingResponse(
            iter(["data: Error: prompt is required\n\n", "data: [DONE]\n\n"]),
            media_type="text/event-stream"
        )
    
    print(f"\n[INFO] Received prompt: {user_prompt[:100]}...")
    
    # In production, these would come from authentication/login
    # For now, generate unique session IDs per request
    import uuid
    session_id = f"session_{uuid.uuid4()}"
    user_id = "default_user"

    return StreamingResponse(
        agent_response_generator(user_prompt=user_prompt, session_id=session_id, user_id=user_id),
        media_type="text/event-stream"
    )


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify server is running.
    """
    return {"status": "healthy", "message": "JARVIS is online"}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*50)
    print("Starting JARVIS FastAPI Server")
    print("="*50)
    print("Available endpoints:")
    print("  POST /api/chat - Send user prompt to agent")
    print("  GET  /api/health - Check server health")
    print("="*50 + "\n")

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)