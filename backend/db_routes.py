"""
db_routes.py
------------
Non-invasive router: plugs your LangGraph pipeline + PostgreSQL logging
into your EXISTING FastAPI app. Does NOT touch your frontend, LangGraph,
RAG, or LLM code — only calls into Graph.graph exactly like app.py does.

In your existing FastAPI file, add:
    from db_routes import router as db_router
    app.include_router(db_router)
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud import get_or_create_user, create_query, create_response
from Graph import graph
from state import validate_initial_state
from exception import ProjectError

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    email: str
    query: str
    file_path: Optional[str] = None


class ReviewRequest(BaseModel):
    thread_id: str
    query_id: int
    approved: bool
    feedback: Optional[str] = None


def _format_interrupt(result: dict, thread_id: str, query_id: int) -> dict:
    interrupt_data = result["__interrupt__"][0].value
    return {
        "status": "pending_review",
        "thread_id": thread_id,
        "query_id": query_id,
        "draft_response": interrupt_data["response"],
    }


@router.post("/start")
async def start_chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Runs the pipeline. Logs the user + query immediately.
    If the pipeline pauses for human review, returns the draft for approval.
    Otherwise logs the final response and returns it directly."""
    user = await get_or_create_user(db, payload.email)
    query_row = await create_query(db, user.user_id, payload.query)

    raw_state = {
        "user_query": payload.query,
        "file_path": payload.file_path,
        "messages": [],
        "retry_count": 0,
    }

    try:
        initial_state = validate_initial_state(raw_state)
    except ProjectError as e:
        return {"status": "error", "detail": str(e)}

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(initial_state, config=config)
    except ProjectError as e:
        return {"status": "error", "detail": str(e)}

    if "__interrupt__" in result:
        return _format_interrupt(result, thread_id, query_row.query_id)

    final_response = result.get("response", "")
    await create_response(db, query_row.query_id, final_response)
    return {"status": "complete", "response": final_response}


@router.post("/review")
async def review_chat(payload: ReviewRequest, db: AsyncSession = Depends(get_db)):
    """Resumes a paused pipeline after the frontend sends the human's
    approve/reject decision. Loops until final, then logs the response."""
    config = {"configurable": {"thread_id": payload.thread_id}}

    try:
        result = graph.invoke(
            Command(resume={"approved": payload.approved, "feedback": payload.feedback or ""}),
            config=config,
        )
    except ProjectError as e:
        return {"status": "error", "detail": str(e)}

    if "__interrupt__" in result:
        return _format_interrupt(result, payload.thread_id, payload.query_id)

    final_response = result.get("response", "")
    await create_response(db, payload.query_id, final_response)
    return {"status": "complete", "response": final_response}