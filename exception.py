"""
exception.py
------------
Centralized exception architecture.

Every custom exception carries structured debugging context:
error_type, file, function, operation, node (LangGraph node, if applicable),
and the original exception (always chained with `from e`, never hidden).

This file ONLY contains exception classes + the node-wrapping decorator.
Actual business logic stays in Nodes.py / Rag.py.
"""

import functools
from langgraph.errors import GraphInterrupt


class ProjectError(Exception):
    """Base exception for the entire project. All custom exceptions inherit from this."""

    def __init__(self, message: str, *, file: str = "", function: str = "",
                 operation: str = "", node: str = "", original_error: Exception = None):
        self.error_type = self.__class__.__name__
        self.file = file
        self.function = function
        self.operation = operation
        self.node = node
        self.original_error = original_error
        super().__init__(self._format(message))

    def _format(self, message: str) -> str:
        lines = [f"[{self.error_type}] {message}"]
        if self.node:
            lines.append(f"Node: {self.node}")
        if self.file:
            lines.append(f"File: {self.file}")
        if self.function:
            lines.append(f"Function: {self.function}()")
        if self.operation:
            lines.append(f"Operation: {self.operation}")
        if self.original_error:
            lines.append(f"Original Error: {self.original_error}")
        return "\n".join(lines)


# ---- State / validation ----
class StateValidationError(ProjectError):
    """Raised when incoming state data fails Pydantic validation."""


# ---- Rag.py / document ingestion ----
class UnsupportedFileTypeError(ProjectError):
    """Raised when an uploaded file has no registered loader."""


class FileLoadError(ProjectError):
    """Raised when a file path does not exist or cannot be opened."""


class DocumentLoadError(ProjectError):
    """Raised when a loader fails to parse a document (PDF/DOCX/PPTX/TXT)."""


class EmptyDocumentError(ProjectError):
    """Raised when no usable text is extracted from a document."""


class ChunkingError(ProjectError):
    """Raised when text splitting fails or produces zero chunks."""


class EmbeddingError(ProjectError):
    """Raised when HuggingFace embedding generation fails."""


class VectorStoreError(ProjectError):
    """Raised when FAISS storage or retriever creation fails."""


class RetrievalError(ProjectError):
    """Raised when retriever.invoke() fails during query time."""


# ---- LangGraph nodes / LLM ----
class LLMError(ProjectError):
    """Raised when an LLM provider call fails or returns unusable output."""


class NodeExecutionError(ProjectError):
    """Generic wrapper for an unexpected/unclassified failure inside a LangGraph node."""


# =========================================================
# Shared utility — decorator that wraps every LangGraph node
# =========================================================

def handle_node_errors(node_name: str):
    """
    Decorator for LangGraph node functions (signature: func(state) -> dict).

    - If the node raises a ProjectError already (from Rag.py, an LLM call, etc.),
      it is passed through unchanged, just tagging the node name if missing.
    - Any other, unexpected exception is wrapped into NodeExecutionError with
      full context (file, function, node) and the original error chained.

    This guarantees no LangGraph node ever produces a bare, confusing traceback.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(state):
            try:
                return func(state)
            except GraphInterrupt:
                # This is LangGraph's own pause/resume control-flow signal
                # (raised by interrupt()) — must NEVER be caught here.
                raise
            except ProjectError as e:
                if not e.node:
                    e.node = node_name
                raise
            except Exception as e:
                raise NodeExecutionError(
                    "Unhandled exception inside node.",
                    file=func.__module__ + ".py",
                    function=func.__name__,
                    operation="node execution",
                    node=node_name,
                    original_error=e,
                ) from e
        return wrapper
    return decorator


class RagOperationError(ProjectError):
    """Raised when any step inside a Rag.py function fails unexpectedly."""


def handle_rag_errors(function_name: str, file: str = "Rag.py"):
    """
    Decorator for Rag.py functions (e.g. build_retriever).
    Same philosophy as handle_node_errors: wrap the WHOLE function once,
    don't scatter try/except inside the business logic.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ProjectError as e:
                if not e.function:
                    e.function = function_name
                if not e.file:
                    e.file = file
                raise
            except Exception as e:
                raise RagOperationError(
                    "Unhandled exception inside Rag.py operation.",
                    file=file,
                    function=function_name,
                    operation="rag pipeline step",
                    original_error=e,
                ) from e
        return wrapper
    return decorator