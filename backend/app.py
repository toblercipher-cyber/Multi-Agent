"""
app.py
------
FastAPI web layer for the existing LangGraph pipeline.

Architecture:
    Frontend  ->  FastAPI (this file)  ->  Graph.py  ->  Nodes.py / Rag.py / LLM.py  ->  response

This file is a thin API shell. It does NOT re-implement any RAG or LangGraph
logic — it reuses the already-compiled `graph` from Graph.py plus the existing
`validate_initial_state` / `ProjectError` machinery.

Endpoints:
    GET  /                          health check
    POST /upload                    upload PDF/DOCX/PPTX/TXT, returns a saved file path
    POST /chat                      submit a question (optionally about an uploaded file)
    POST /chat/{thread_id}/review   approve / reject the human-in-the-loop draft

Why a review endpoint exists:
    The graph pauses at Human_Review_Node via interrupt(). Because that thread
    state lives in the graph's in-process MemorySaver checkpointer, POST /chat
    returns a `pending_review` payload carrying the thread_id, and
    POST /chat/{thread_id}/review resumes that same thread with the decision.
    This keeps the existing human-in-the-loop node working over HTTP with zero
    changes to Graph.py / Nodes.py.

NOTE: MemorySaver is per-process, so run uvicorn with a single worker (the
default). A multi-worker deployment would need a shared checkpointer.
"""

import os
import shutil
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from pydantic import BaseModel, Field, field_validator

# Allow importing the sibling modules (Graph.py, state.py, exception.py) both as
# `uvicorn app:app` from inside backend/ and `uvicorn backend.app:app` from root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from exception import (  # noqa: E402  (imports after sys.path setup)
    ProjectError,
    StateValidationError,
    UnsupportedFileTypeError,
    FileLoadError,
    DocumentLoadError,
    EmptyDocumentError,
    ChunkingError,
    EmbeddingError,
    VectorStoreError,
    RetrievalError,
    LLMError,
    NodeExecutionError,
    RagOperationError,
)
from Graph import graph  # noqa: E402
from state import validate_initial_state  # noqa: E402
from db_routes import router as db_router  # noqa: E402 (PostgreSQL logging endpoints)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BuildHub AI Agent API",
    description=(
        "FastAPI layer over the existing LangGraph pipeline. Upload a document "
        "(PDF/DOCX/PPTX/TXT), then ask questions about it — or ask a general "
        "question without a file."
    ),
    version="1.0.0",
)

# CORS — the frontend is served from a different origin during dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL-backed endpoints (/api/chat/start, /api/chat/review) from db_routes.py.
# Registered only after `app` exists — must never be moved above this line.
app.include_router(db_router)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Demo credentials — the same values pre-filled in the login form. No user store
# exists yet, so auth validates against this demo account. Override via env vars.
DEMO_LOGIN_EMAIL = os.getenv("DEMO_LOGIN_EMAIL", "elissesmorisev@gmail.com")
DEMO_LOGIN_PASSWORD = os.getenv("DEMO_LOGIN_PASSWORD", "redrose2026")


# ---------------------------------------------------------------------------
# Pydantic models (structured requests)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    user_query: str = Field(..., min_length=1, description="The user's question.")
    file_path: str | None = Field(
        None,
        description="Absolute path returned by POST /upload, or omit for a general question.",
    )

    @field_validator("user_query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("user_query cannot be blank or whitespace-only.")
        return v


class ReviewRequest(BaseModel):
    approved: bool = Field(..., description="True to accept the draft, False to request a revision.")
    feedback: str = Field(default="", description="Feedback used to rewrite the draft when approved=False.")


class LoginRequest(BaseModel):
    email: str = Field(..., description="The user's email address.")
    password: str = Field(..., description="The user's password.")

    @field_validator("email")
    @classmethod
    def strip_email(cls, v: str) -> str:
        return v.strip()


class LoginResponse(BaseModel):
    status: str = Field(..., description="'success' when the credentials match.")
    email: str = Field(default="", description="The authenticated email address.")
    message: str = Field(default="", description="Human-readable hint.")


class ChatResponse(BaseModel):
    status: str = Field(
        ...,
        description="'completed' (final answer) or 'pending_review' (draft awaiting approval).",
    )
    thread_id: str = Field(
        ...,
        description="Thread id. Pass it to POST /chat/{thread_id}/review when status='pending_review'.",
    )
    response: str = Field(default="", description="The final answer, or the draft awaiting review.")
    message: str = Field(default="", description="Optional human-readable hint.")


class UploadResponse(BaseModel):
    file_id: str = Field(..., description="Unique id for this upload.")
    file_path: str = Field(
        ...,
        description="Absolute path on the server. Pass this back to POST /chat as file_path.",
    )
    filename: str = Field(..., description="Original file name.")
    content_type: str = Field(..., description="MIME type reported by the client.")
    size: int = Field(..., description="Size of the saved file in bytes.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _status_code(error: ProjectError) -> int:
    """Maps a ProjectError subclass to an appropriate HTTP status code."""
    if isinstance(error, StateValidationError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    if isinstance(error, UnsupportedFileTypeError):
        return status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    if isinstance(error, FileLoadError):
        return status.HTTP_404_NOT_FOUND
    # Everything below is a server-side failure inside the RAG / LLM / graph layer.
    if isinstance(
        error,
        (
            DocumentLoadError,
            EmptyDocumentError,
            ChunkingError,
            EmbeddingError,
            VectorStoreError,
            RetrievalError,
            LLMError,
            NodeExecutionError,
            RagOperationError,
        ),
    ):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _raise_http(error: ProjectError):
    """Raises the mapped HTTPException for any ProjectError from the existing layer."""
    raise HTTPException(
        status_code=_status_code(error),
        detail={
            "error_type": error.error_type,
            "message": error.args[0] if error.args else str(error),
            "node": error.node,
            "operation": error.operation,
        },
    )


def _invoke_graph(input, config) -> dict:
    """Runs graph.invoke() and converts ProjectError / unexpected errors to HTTP."""
    try:
        return graph.invoke(input, config=config)
    except ProjectError as e:
        _raise_http(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UnexpectedError", "message": str(e)},
        )


def _build_chat_response(result: dict, thread_id: str) -> ChatResponse:
    """Turns a graph result into a ChatResponse, detecting interrupt() pauses."""
    if "__interrupt__" in result:
        pending = result["__interrupt__"][0].value
        return ChatResponse(
            status="pending_review",
            thread_id=thread_id,
            response=pending.get("response", ""),
            message="Draft generated but awaiting review — call POST /chat/{thread_id}/review.",
        )
    return ChatResponse(
        status="completed",
        thread_id=thread_id,
        response=result.get("response", ""),
        message="",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
def health():
    return {"status": "ok", "service": "BuildHub AI Agent API", "docs": "/docs"}


@app.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document (PDF / DOCX / PPTX / TXT)",
)
async def upload_document(file: UploadFile = File(...)):
    original_name = Path(file.filename or "").name
    ext = Path(original_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error_type": "UnsupportedFileTypeError",
                "message": (
                    f"Unsupported file type '{ext or '(none)'}'. "
                    f"Allowed extensions: {sorted(ALLOWED_EXTENSIONS)}."
                ),
            },
        )

    # The Rag loader switches on the file extension, so the saved file must keep it.
    file_id = uuid.uuid4().hex
    dest = UPLOAD_DIR / f"{file_id}{ext}"

    try:
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "UploadError", "message": f"Failed to save upload: {e}"},
        )

    return UploadResponse(
        file_id=file_id,
        file_path=str(dest.resolve()),
        filename=original_name or dest.name,
        content_type=file.content_type or "application/octet-stream",
        size=dest.stat().st_size,
    )


@app.post("/chat", response_model=ChatResponse, summary="Submit a question (optionally about an uploaded file)")
def chat(payload: ChatRequest):
    if payload.file_path and not Path(payload.file_path).is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_type": "FileLoadError",
                "message": f"Uploaded file no longer exists on the server: {payload.file_path}",
            },
        )

    raw_state = {
        "user_query": payload.user_query,
        "file_path": payload.file_path,
        "messages": [],
        "retry_count": 0,
    }

    try:
        initial_state = validate_initial_state(raw_state)
    except ProjectError as e:
        _raise_http(e)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = _invoke_graph(initial_state, config)
    return _build_chat_response(result, thread_id)


@app.post(
    "/chat/{thread_id}/review",
    response_model=ChatResponse,
    summary="Approve or reject a draft that is awaiting human review",
)
def review_draft(thread_id: str, payload: ReviewRequest):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = graph.invoke(
            Command(resume={"approved": payload.approved, "feedback": payload.feedback}),
            config=config,
        )
    except ProjectError as e:
        _raise_http(e)
    except Exception as e:
        # LangGraph raises here if the thread is unknown / not awaiting review.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_type": "ThreadStateError",
                "message": (
                    f"Cannot resume thread '{thread_id}' — it may not exist in this "
                    f"server process or is not awaiting review. ({e})"
                ),
            },
        )
    return _build_chat_response(result, thread_id)


@app.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate a user",
    description="Validates credentials against the configured demo account.",
)
def login(payload: LoginRequest):
    if payload.email.lower() == DEMO_LOGIN_EMAIL.lower() and payload.password == DEMO_LOGIN_PASSWORD:
        return LoginResponse(
            status="success",
            email=payload.email,
            message="Login successful",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error_type": "InvalidCredentials",
            "message": "Invalid email or password.",
        },
    )


# ---------------------------------------------------------------------------
# /api aliases — the frontend calls these paths. They reuse the exact same
# handlers as the unprefixed routes (no duplicated logic).
# ---------------------------------------------------------------------------

api_router = APIRouter(prefix="/api")
api_router.add_api_route(
    "/upload",
    upload_document,
    methods=["POST"],
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document (PDF / DOCX / PPTX / TXT)",
)
api_router.add_api_route(
    "/chat",
    chat,
    methods=["POST"],
    response_model=ChatResponse,
    summary="Submit a question (optionally about an uploaded file)",
)
api_router.add_api_route(
    "/chat/{thread_id}/review",
    review_draft,
    methods=["POST"],
    response_model=ChatResponse,
    summary="Approve or reject a draft that is awaiting human review",
)
api_router.add_api_route(
    "/login",
    login,
    methods=["POST"],
    response_model=LoginResponse,
    summary="Authenticate a user",
)
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)