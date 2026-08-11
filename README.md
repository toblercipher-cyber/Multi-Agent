# 🧠 Enterprise AI Knowledge Hub

An end-to-end AI-powered knowledge management and document analysis system built with **LangChain, LangGraph, FastAPI, PostgreSQL, ChromaDB, and HuggingFace embeddings**.

The system allows users to upload documents, retrieve relevant information using RAG, generate AI responses, and optionally send responses through a **Human-in-the-Loop approval/rejection workflow** before returning the final answer.

The project is designed with a modular backend architecture and a separate frontend, providing a practical example of how modern Generative AI applications can be structured for real-world use.

---

## 🚀 Key Features

### 📄 Multi-Format Document Processing

Supports:

- PDF
- DOCX
- PPTX
- TXT

Uploaded documents are processed, converted into text, chunked, embedded, and stored for semantic retrieval.

---

### 🔎 Retrieval-Augmented Generation

The application uses a RAG pipeline to:

1. Process uploaded documents
2. Extract text
3. Clean and normalize content
4. Split documents into chunks
5. Generate embeddings
6. Store embeddings in ChromaDB
7. Retrieve relevant context
8. Generate context-aware AI responses

---

### 🧠 LangGraph Workflow

LangGraph is used to orchestrate the AI workflow.

The project includes workflow concepts such as:

- Sequential processing
- Conditional routing
- Iterative retrieval
- Parallel processing
- Human-in-the-Loop
- Interrupt and resume workflow

The Human-in-the-Loop system can pause the workflow when review is required and resume it after the user approves or rejects the generated response.

---

### 👤 Human-in-the-Loop

The application supports AI response review.

Workflow:

```text
User Query
     ↓
RAG Retrieval
     ↓
LLM Response
     ↓
Human Review
     ↓
 ┌───────────────┐
 │               │
Approve        Reject
 │               │
 ↓               ↓
Complete    Feedback
                 ↓
          Workflow Resumes
                 ↓
          Revised Response
