<img width="1346" height="612" alt="support_page_user_feed_back" src="https://github.com/user-attachments/assets/477f4f85-4a48-4b3f-8b12-129480d595cc" />


<img width="1342" height="608" alt="Support_page_2" src="https://github.com/user-attachments/assets/f3ed8390-3c0b-43eb-8e12-62433ba4c06c" />


<img width="1340" height="614" alt="Suppport_page" src="https://github.com/user-attachments/assets/9b56997c-fac2-47fc-b86a-273cc4858853" />


<img width="1360" height="606" alt="human_approval_for_this_report" src="https://github.com/user-attachments/assets/91efb7b4-30f0-432f-94bf-d18e60e8b0e5" />


<img width="1359" height="604" alt="proper-OUTPUT-2" src="https://github.com/user-attachments/assets/40e7a3ab-bc7f-4f47-a225-95a98b21eea9" />


<img width="1360" height="612" alt="Proper_output_of_my_chatbot" src="https://github.com/user-attachments/assets/59cbcae7-ab41-407e-9c41-a5533b6c3a53" />


<img width="1357" height="612" alt="Generated_the_proper_report_on_this" src="https://github.com/user-attachments/assets/91f114bc-4378-4bde-be4b-5a21d75bb1a0" />


<img width="1356" height="614" alt="Chatbot_loading_scene" src="https://github.com/user-attachments/assets/5048072c-4eaa-45b0-a739-48d3210bc301" />


<img width="1360" height="613" alt="Human_in_the_loop_Multiagent" src="https://github.com/user-attachments/assets/92b41c3b-c4ee-453e-a094-11aa93366a71" />


<img width="1354" height="610" alt="Multiagent_chatbot_qurie" src="https://github.com/user-attachments/assets/7b262a38-a2a6-4871-85a1-38f6ae58720d" />


<img width="1348" height="616" alt="Multiagent_login_12" src="https://github.com/user-attachments/assets/511b76d4-9ee8-406e-9797-f695b4a26fdc" />


<img width="1356" height="609" alt="Multiagent_Login_1" src="https://github.com/user-attachments/assets/8ab2281d-4504-4fe1-8bbb-766428d624ff" />


<img width="1345" height="611" alt="Multiagent_L_3" src="https://github.com/user-attachments/assets/93ef2305-5699-43ad-96f5-d7ddd3ba4dc1" />


<img width="1329" height="608" alt="Multiagent_L_2" src="https://github.com/user-attachments/assets/6b014005-db8a-40c7-8a09-23647ee58f70" />

<img width="1348" height="588" alt="MultiAgent_L_1" src="https://github.com/user-attachments/assets/4f1244ed-9d31-48bc-9718-b90c11b433f7" />



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

