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






🗄️ PostgreSQL Database

PostgreSQL is used for persistent application data.

The current database architecture contains three primary tables:

users
   │
   └──────< user_queries
                    │
                    └──────< llm_responses
Users

Stores user authentication information.

User Queries

Stores questions submitted by users.

LLM Responses

Stores AI-generated responses associated with user queries.

This allows the application to maintain a relationship between:

User
 ↓
Query
 ↓
AI Response






⚡ FastAPI Backend

FastAPI provides the API layer between the frontend and AI backend.

Current API routes include:

POST /api/login
POST /api/upload
POST /api/chat/start
POST /api/chat/review

Architecture:

Frontend
    ↓
FastAPI
    ↓
LangGraph
    ↓
LangChain / RAG
    ↓
LLM
    ↓
PostgreSQL
    ↓
Response
    ↓
Frontend






-SYSTEM-ARCHITECHTURE :-

                         ┌─────────────────────┐
                         │      Frontend       │
                         │ HTML / CSS / JS     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │      API Layer      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     LangGraph       │
                         │ Workflow Engine     │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
                RAG Pipeline     LLM Layer      Human Review
                    │               │                │
                    ▼               ▼                │
               ChromaDB        AI Response           │
                    │               │                │
                    └───────────────┼────────────────┘
                                    │
                                    ▼
                              PostgreSQL
                                    │
                                    ▼
                               Final Result


-PROJECT-ARCHITECHTURE :-

Enterprise-AI-Knowledge-Hub/
│
├── backend/
│   │
│   ├── app.py
│   ├── Graph.py
│   ├── Nodes.py
│   ├── Rag.py
│   ├── LLM.py
│   ├── state.py
│   ├── exception.py
│   │
│   └── database/
│       └── PostgreSQL related files
│
├── frontend/
│   │
│   ├── landing_page.html
│   ├── login.html
│   ├── chat.html
│   ├── support.html
│   │
│   ├── OTF/
│   ├── TTF/
│   └── WEB/
│
├── requirements.txt
├── .env
└── README.md


-DOCUMENT-PROCESSING-WORKFLOW :-


User Uploads Document
        │
        ▼
File Validation
        │
        ▼
File-Type Detection
        │
        ├── PDF
        ├── DOCX
        ├── PPTX
        └── TXT
        │
        ▼
Text Extraction
        │
        ▼
Text Cleaning
        │
        ▼
Document Chunking
        │
        ▼
HuggingFace Embeddings
        │
        ▼
ChromaDB
        │
        ▼
Knowledge Base Ready


-💬 Query Processing Workflow:  :-


User Question
      │
      ▼
Query Analysis
      │
      ▼
Retrieve Relevant Context
      │
      ▼
Context Evaluation
      │
      ├───────────────┐
      │               │
   Insufficient     Sufficient
      │               │
      ▼               ▼
Query Optimization  Continue
      │
      ▼
Additional Retrieval
      │
      └─────── Loop ───────┘
                      │
                      ▼
              Parallel Processing
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Citation     Metadata    Prompt
      Processing   Processing  Building
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
                Context Merge
                      │
                      ▼
                 LLM Response
                      │
                      ▼
              Human Review
                 │       │
              Approve   Reject
                 │       │
                 ▼       ▼
             Complete  Feedback
                           │
                           ▼
                    Workflow Resume
                           │
                           ▼
                    Revised Response


-> 🧩 Technology Stack
Backend
Python
FastAPI
LangChain
LangGraph
Pydantic
PostgreSQL
Generative AI
Large Language Models
Retrieval-Augmented Generation (RAG)
HuggingFace Embeddings
LangChain Runnables
Prompt Templates
Iterative Retrieval
Human-in-the-Loop workflows
Vector Database
ChromaDB
Document Processing
PDF processing
DOCX processing
PPTX processing
TXT processing
Frontend
HTML5
CSS3
JavaScript
Database
PostgreSQL
🔐 Error Handling

The backend includes centralized exception handling.

The system is designed to provide useful error information while preventing sensitive information such as API keys and environment variables from being exposed.

Errors can be traced back to their originating backend component and function.



🧪 Testing

The application has been tested across the major end-to-end workflows.

Authentication
Valid Login       → 200 ✅
Invalid Login     → 401 ✅
File Upload
PDF      → 201 ✅
DOCX     → 201 ✅
PPTX     → 201 ✅
TXT      → 201 ✅
Invalid  → 415 ✅
AI Workflow
General Chat              → Complete ✅
Document Chat             → Pending Review ✅
Human Approval            → Complete ✅
Human Rejection           → Revised Response ✅
Interrupt / Resume        → Working ✅
PostgreSQL
User Data       → Stored ✅
User Queries    → Stored ✅
LLM Responses   → Stored ✅
API Verification

The frontend uses the following API routes:

POST /api/login
POST /api/upload
POST /api/chat/start
POST /api/chat/review
⚙️ Installation
1. Clone the Repository
git clone <YOUR_REPOSITORY_URL>
cd Enterprise-AI-Knowledge-Hub
2. Create a Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / macOS
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
pip install -r requirements.txt
4. Configure Environment Variables

Create a .env file.

Example:

DATABASE_URL=your_postgresql_connection_string

LLM_API_KEY=your_api_key

HUGGINGFACE_API_KEY=your_api_key

Use the actual environment variable names required by your implementation.

Never commit .env to GitHub.

Add it to .gitignore:

.env
venv/
__pycache__/
*.pyc

▶️ Running the Backend

Start the FastAPI application using your project's configured entry point.

For example:

uvicorn backend.app:app --reload

The API will be available at:

http://127.0.0.1:8000

FastAPI Swagger documentation:

http://127.0.0.1:8000/docs
🖥️ Running the Frontend

Open the frontend through your preferred local development server.

The main application flow is:

Landing Page
      ↓
Login
      ↓
AI Chat
      ↓
Support
🔑 API Overview
Method	Endpoint	Purpose
POST	/api/login	Authenticate user
POST	/api/upload	Upload supported documents
POST	/api/chat/start	Start AI query and persist query/response
POST	/api/chat/review	Approve/reject and resume AI workflow
📚 Supported Files
File Type	Supported
PDF	✅
DOCX	✅
PPTX	✅
TXT	✅
🎯 Project Goals

This project was developed to demonstrate practical implementation of modern Generative AI engineering concepts, including:

RAG architecture
Vector databases
Document processing
LangChain
LangGraph
FastAPI
PostgreSQL
Embeddings
Prompt engineering
Iterative retrieval
Human-in-the-Loop workflows
API integration
Exception handling
Modular Python architecture

The primary goal is to bridge the gap between AI tutorials and production-style AI application development.

🚧 Future Improvements

Possible future improvements include:

Streaming LLM responses
Advanced authentication
Role-based access control
Document management
Improved retrieval evaluation
Observability and tracing
Cloud deployment
Automated testing
Production-grade authentication
Additional document formats
👨‍💻 Author

Syed Abdul Rehman

Built as an AI Engineering project focused on combining:

Python
+
LangChain
+
LangGraph
+
RAG
+
FastAPI
+
PostgreSQL
+
Generative AI
⭐ Project Status

Status: Completed / Portfolio Ready

The current implementation successfully demonstrates an end-to-end Generative AI workflow with document ingestion, RAG, LangGraph orchestration, Human-in-the-Loop review, FastAPI APIs, and PostgreSQL persistence.


### GitHub topics

I'd also add these to the repository:

```text
python
fastapi
langchain
langgraph
rag
generative-ai
llm
postgresql
chromadb
huggingface
human-in-the-loop
artificial-intelligence
ai-engineering

