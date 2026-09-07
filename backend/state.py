"""
state.py
--------
State has two parts:

1. `State` (TypedDict) — the actual LangGraph state schema. Left AS-IS so
   every existing node (state["field"]) keeps working with zero changes.

2. `StateInput` (Pydantic model) — validates the initial payload BEFORE it
   is handed to graph.invoke(), so invalid data never reaches a node.
   Call `validate_initial_state(raw_dict)` at the entry point (app.py).
"""

from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, field_validator

from exception import StateValidationError

#-----------x------------------x----------------------x-----------------------x----------------------------x------------------x------------


class State(TypedDict):
    # Input
    user_query: str
    file_path: str
    messages: Annotated[list[BaseMessage], add_messages]

    # Query processing
    rewritten_query: str
    query_intent: str

    # Document ingestion / retrieval
    file_type: str
    extracted_raw_text: str
    cleaned_text: str
    chunks: list[str]
    retrieved_chunks: list[str]

    # Iterative retrieval loop
    context_sufficient: str
    retry_count: int

    # Parallel processing
    citations: str
    metadata: str
    final_prompt: str
    merged_context: str

    # Output
    response: str

    # Human review
    approved: bool
    reviewer_feedback: str

    # Error handling
    error: str


# =========================================================
# Pydantic input validation — runs once, before graph.invoke()
# =========================================================

class StateInput(BaseModel):
    user_query: str = Field(..., min_length=1)
    file_path: Optional[str] = None
    retry_count: int = Field(default=0, ge=0)

    @field_validator("user_query")
    @classmethod
    def query_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("user_query cannot be blank or whitespace-only.")
        return v

    @field_validator("file_path")
    @classmethod
    def file_path_not_blank_if_given(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("file_path cannot be an empty string — omit it instead.")
        return v


def validate_initial_state(raw: dict) -> dict:
    """
    Validates the raw input dict (from app.py) before it enters the graph.
    Raises StateValidationError (chained) on any invalid field.
    Returns the validated dict, ready to pass into graph.invoke().
    """
    try:
        validated = StateInput(**raw)
    except Exception as e:
        raise StateValidationError(
            "Initial state failed validation.",
            file="state.py",
            function="validate_initial_state",
            operation="Pydantic validation",
            original_error=e,
        ) from e

    return {**raw, **validated.model_dump(exclude_none=True)}