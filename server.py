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
    user_message = Content(
        role="user",
        parts=[Part(text=user_prompt)],
    )
    
    await get_or_create_session("jarvis_app", session_id, user_id)
    try:
        async for event in jarvis_runner.run_async(
            new_message=user_message,
            session_id=session_id,
            user_id=user_id
        ):
            if event.content and event.content.role == "model" and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield f"data: {part.text}\n"
    except Exception as e:
        yield f"data: Error during agent run: {str(e)}\n"


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    API for chatting with user, when user enters a prompt this function gets executed in the background
    """

    try:
        data = await request.json()
        user_prompt = data.get("prompt")
    except json.JSONDecodeError:
        return StreamingResponse(iter(["data: Error: Invalid JSON in request\n"]))
    
    if not user_prompt:
        return StreamingResponse(iter(["data: error: prompt is required\n"]))
    
    # in real application this ids would come from different real users (via login page)
    session_id = "this_should_be_unique(todo...)"
    user_id = "this_should_not_be_unique"

    return StreamingResponse(
        agent_response_generator(user_prompt=user_prompt, session_id=session_id, user_id=user_id),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
