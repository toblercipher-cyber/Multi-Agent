# build Nodes according to our project plan :
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langchain_core.prompts import PromptTemplate
from state import State
from LLM import llm_1, llm_2, llm_3
from Rag import build_retriever
from langgraph.types import interrupt
from exception import handle_node_errors
#x----------------x--------------------x--------------------x-------------------------x----------------------------------x-------

def extract_text(content) -> str:
    """Gemini sometimes returns content as a list of dicts instead of a plain
    string. This normalizes either shape into clean text."""
    if isinstance(content, list):
        return "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        ).strip()
    return content.strip()


def truncate_context(text: str, max_chars: int = 2000) -> str:
    """Caps how much context gets sent per LLM call — the same retrieved
    context is reused across 3+ parallel calls, so keeping it short avoids
    blowing through per-minute token limits (esp. Groq's 8000 TPM)."""
    return text if len(text) <= max_chars else text[:max_chars] + "..."


def invoke_with_fallback(prompt: str, primary=llm_3, fallback=llm_1):
    """Tries the primary LLM first. If it fails for ANY reason (quota,
    rate limit, downtime), automatically retries once on the fallback LLM
    instead of crashing the whole node."""
    try:
        return primary.invoke(prompt)
    except Exception:
        return fallback.invoke(prompt)


@handle_node_errors("query_optimizer")
def Query_Optimizer_Model(state: State) -> dict:
    """Optimizes the user query for better retrieval performance."""
    user_query = state["user_query"]
    prompt = (
        f"You are an expert search-query optimizer for a document retrieval system "
        f"that uses semantic (embedding-based) search over chunked documents.\n\n"
        f"Your job is to rewrite the user's raw question into a query that will match "
        f"relevant document chunks as closely as possible. Follow these rules:\n"
        f"1. Preserve the original meaning and intent completely — do not change what is being asked.\n"
        f"2. Expand vague or casual phrasing into clear, specific, keyword-rich language.\n"
        f"3. Include likely synonyms or alternate terms for key concepts, since the exact "
        f"wording in the document may differ from the user's wording.\n"
        f"4. Remove filler words, greetings, and conversational phrasing that add no search value.\n"
        f"5. Keep it as a single, well-formed question or phrase — not a list, not bullet points.\n"
        f"6. Do NOT invent new facts, requirements, or constraints that the user did not ask for.\n\n"
        f"Original user query: '{user_query}'\n\n"
        f"Respond with ONLY the rewritten query text. No explanation, no quotation marks, "
        f"no preamble — just the optimized query itself."
    )
    result = llm_2.invoke(prompt)
    optimized_query = result.content.strip()
    return {"rewritten_query": optimized_query}


@handle_node_errors("query_classification")
def Query_Classification_Model(state: State) -> dict:
    """Classifies whether the query needs document retrieval or is a general question."""
    rewritten_query = state["rewritten_query"]
    has_file = bool(state.get("file_path"))
    prompt = (
        f"You are a routing classifier for an AI assistant that can either (a) answer "
        f"questions using an uploaded document, or (b) answer general conversational "
        f"questions using its own knowledge.\n\n"
        f"Decide which path this query belongs to, using these rules:\n"
        f"- If a file has been uploaded (see 'File uploaded' below) AND the question could "
        f"reasonably be answered from a document's content, classify it as 'document'.\n"
        f"- If no file was uploaded, OR the question is small talk, a greeting, a general "
        f"knowledge question, or clearly unrelated to any document content, classify it as 'general'.\n"
        f"- When in doubt and a file IS uploaded, prefer 'document' — it is safer to check "
        f"the document than to skip it.\n\n"
        f"File uploaded: {has_file}\n"
        f"Query: '{rewritten_query}'\n\n"
        f"Respond with ONLY one lowercase word — either: document OR general. "
        f"No punctuation, no explanation, nothing else."
    )
    result = llm_1.invoke(prompt)
    intent = result.content.strip().lower()
    return {"query_intent": intent}


@handle_node_errors("document_loader")
def Document_Loader(state: State) -> dict:
    """Loads and extracts relevant text from any supported file (PDF/DOCX/PPTX/TXT)."""
    retriever = build_retriever(state["file_path"])
    context = "\n\n".join(
        doc.page_content for doc in retriever.invoke(state["rewritten_query"])
    )
    return {"extracted_raw_text": context}


#This node represent as out iterative workflow .

@handle_node_errors("context_evaluation")
def Context_Evaluation_Model(state: State) -> dict:
    """Evaluates whether the retrieved context is sufficient to answer the query."""
    context = state["extracted_raw_text"]
    rewritten_query = state["rewritten_query"]
    prompt = (
        f"You are a strict but fair quality-control reviewer for a document retrieval "
        f"system. Your ONLY job is to decide whether the retrieved context below contains "
        f"enough information to write a complete, accurate answer to the query.\n\n"
        f"Evaluation guidelines:\n"
        f"- Mark it 'sufficient' if the context contains information that directly answers "
        f"the query, OR contains enough related information that a reasonable, well-supported "
        f"answer can be constructed from it — even if it is not phrased exactly like the query.\n"
        f"- Do NOT require the context to be a perfect, word-for-word match. Partial but "
        f"relevant and usable information still counts as 'sufficient'.\n"
        f"- Mark it 'insufficient' ONLY if the context is empty, completely unrelated to the "
        f"query, or so vague/fragmented that no meaningful answer could honestly be written from it.\n"
        f"- Do not be overly cautious — if there is reasonable material to work with, choose 'sufficient'.\n\n"
        f"Query: '{rewritten_query}'\n\n"
        f"Retrieved Context:\n{context}\n\n"
        f"Respond with ONLY one lowercase word — either: sufficient OR insufficient. "
        f"No punctuation, no explanation, nothing else."
    )
    result = llm_1.invoke(prompt)
    verdict = result.content.strip().lower()
    retry_count = state.get("retry_count", 0)
    new_retry_count = retry_count + 1 if verdict == "insufficient" else retry_count

    print(f"[Context_Evaluation_Model] verdict='{verdict}' | retry_count={new_retry_count}")

    return {
        "context_sufficient": verdict,
        "retry_count": new_retry_count,
    }


@handle_node_errors("general_question")
def General_Question(state: State) -> dict:
    """Handles general questions using the fallback LLM."""
    user_query = state["user_query"]
    last_message = state["messages"][-1] if state["messages"] else None
    prompt = (
        f"You are a helpful, knowledgeable AI assistant having a normal conversation "
        f"with the user. This question does NOT relate to any uploaded document — answer "
        f"it directly and naturally using your own general knowledge.\n\n"
        f"Guidelines:\n"
        f"- Be clear, accurate, and conversational.\n"
        f"- If relevant, use the previous message below to keep context/continuity.\n"
        f"- Keep the answer focused and easy to read — avoid unnecessary padding.\n\n"
        f"Previous message: {last_message.content if last_message else 'None'}\n\n"
        f"Question: {user_query}"
    )
    result = invoke_with_fallback(prompt)
    return {
        "response": extract_text(result.content),
        "messages": [result],
    }


@handle_node_errors("response_generation")
def Response_Generation_Model(state: State) -> dict:
    """Generates a response based on the merged context, chat history, and user query."""
    context = state["merged_context"]
    user_query = state["user_query"]
    last_message = state["messages"][-1] if state["messages"] else None
    prompt = (
        f"You are a professional AI assistant writing the FINAL answer for the user. "
        f"You have been given verified context (retrieved document content, citations, "
        f"and metadata) that has already been checked for relevance — trust it and use it "
        f"as your primary source of truth.\n\n"
        f"Guidelines for your answer:\n"
        f"1. Answer the user's question directly and completely using the context provided.\n"
        f"2. Structure the answer clearly — use headings, bullet points, or tables where they "
        f"genuinely improve readability, but don't over-format simple answers.\n"
        f"3. If the context includes citations or sources, reference them naturally where helpful.\n"
        f"4. Do not fabricate information that isn't supported by the context.\n"
        f"5. Maintain a professional, clear, and helpful tone throughout.\n"
        f"6. If relevant, use the previous message to maintain conversational continuity.\n\n"
        f"Context:\n{context}\n\n"
        f"Previous message: {last_message.content if last_message else 'None'}\n\n"
        f"Question: {user_query}"
    )
    result = invoke_with_fallback(prompt)
    return {
        "response": extract_text(result.content),
        "messages": [result],
    }


def route_by_query_intent(state: State) -> str:
    """Router — if a file was provided, always use it (don't trust LLM guesswork).
    Only fall back to general_question when no file exists at all."""
    if state.get("file_path"):
        return "document_loader"
    return "general_question"


#This Node is specifically for Loop back if the context is insufficient for answering the query.

def route_by_context_sufficiency(state: State):
    """Loops back if insufficient; fans out to parallel nodes if sufficient."""
    if state["context_sufficient"] == "sufficient" or state.get("retry_count", 0) >= 3:
        return ["citation_model", "metadata_model", "prompt_builder_model"]
    return "query_optimizer"

#x----------------------x--------------------x--------------------------x----------------------x---------------------x-------------------

#prallel workflows - nodes :-

@handle_node_errors("citation_model")
def Citation_Model(state: State) -> dict:
    """Extracts source references/citations from the retrieved context."""
    context = truncate_context(state["extracted_raw_text"])
    prompt = (
        f"You are a citation-extraction assistant. Read the retrieved context below and "
        f"identify the key sources, sections, headings, or document parts this information "
        f"appears to come from.\n\n"
        f"Guidelines:\n"
        f"- List each distinct source or section on its own line.\n"
        f"- If the context includes section titles, page markers, or headings, use those as "
        f"the citation label.\n"
        f"- If no explicit source markers exist, briefly describe where in the document this "
        f"content likely belongs (e.g. 'Introduction section', 'Table describing X').\n"
        f"- Keep each citation short and clear — this is a reference list, not a summary.\n"
        f"- If truly nothing citable is identifiable, respond with 'No clear citations found.'\n\n"
        f"Context:\n{context}"
    )
    result = llm_1.invoke(prompt)
    return {"citations": extract_text(result.content)}


@handle_node_errors("metadata_model")
def Metadata_Model(state: State) -> dict:
    """Extracts metadata such as document type, key topics, and tags."""
    context = truncate_context(state["extracted_raw_text"])
    prompt = (
        f"You are a document metadata analyzer. Read the context below and extract a brief, "
        f"structured summary of what kind of content this is.\n\n"
        f"Provide exactly these three items:\n"
        f"1. Document type — e.g. report, roadmap, contract, research paper, resume, etc.\n"
        f"2. Key topics — 3 to 6 short keywords/phrases covering the main subjects discussed.\n"
        f"3. Relevant tags — a few short labels useful for categorization/search.\n\n"
        f"Keep the whole response brief and scannable — a few lines total, not a full analysis.\n\n"
        f"Context:\n{context}"
    )
    result = llm_2.invoke(prompt)
    return {"metadata": extract_text(result.content)}


@handle_node_errors("prompt_builder_model")
def Prompt_Builder_Model(state: State) -> dict:
    """Builds a structured, optimized prompt for the final response generation step."""
    context = truncate_context(state["extracted_raw_text"])
    rewritten_query = state["rewritten_query"]
    prompt = (
        f"You are a prompt-engineering assistant. Your job is to combine the query and the "
        f"retrieved context below into ONE clear, well-organized block of instructions that "
        f"another AI model will use to write the final answer.\n\n"
        f"Guidelines:\n"
        f"- Clearly restate what question needs to be answered.\n"
        f"- Organize the relevant context underneath it in a clean, readable way (you may "
        f"group related points together, but do not remove important information).\n"
        f"- Do not answer the question yourself — you are only structuring the input for "
        f"the next model.\n"
        f"- Do not add opinions, commentary, or information not present in the context.\n\n"
        f"Query: {rewritten_query}\n"
        f"Context:\n{context}"
    )
    result = llm_1.invoke(prompt)
    return {"final_prompt": extract_text(result.content)}


@handle_node_errors("merge_context")
def Merge_Context(state: State) -> dict:
    """Merges citations, metadata, and final_prompt into one unified context."""
    merged = (
        f"{state['final_prompt']}\n\n"
        f"Citations:\n{state['citations']}\n\n"
        f"Metadata:\n{state['metadata']}"
    )
    return {"merged_context": merged}


@handle_node_errors("human_review")
def Human_Review_Node(state: State) -> dict:
    """Pauses the graph and waits for a human to approve or reject the response."""
    human_input = interrupt({
        "response": state["response"],
        "question": "Approve this response? (approved / rejected + feedback)"
    })
    return {
        "approved": human_input["approved"],
        "reviewer_feedback": human_input.get("feedback", ""),
    }


@handle_node_errors("human_feedback")
def Human_Feedback_Model(state: State) -> dict:
    """Reads reviewer feedback and rewrites the response accordingly."""
    response = state["response"]
    feedback = state["reviewer_feedback"]
    prompt = (
        f"You are revising a previously generated answer based on human reviewer feedback. "
        f"Your job is to rewrite the response so it fully addresses the feedback while "
        f"keeping everything that was already correct and useful.\n\n"
        f"Guidelines:\n"
        f"1. Carefully read the reviewer's feedback and apply every point it raises.\n"
        f"2. Do not remove correct, relevant information just to make changes — only adjust "
        f"what the feedback actually asks for (tone, length, clarity, missing details, etc.).\n"
        f"3. Keep the same professional, clear writing style unless the feedback says otherwise.\n"
        f"4. Produce a complete, standalone answer — not a diff or list of changes.\n\n"
        f"Original response:\n{response}\n\n"
        f"Reviewer feedback:\n{feedback}\n\n"
        f"Write the revised, complete response now."
    )
    result = invoke_with_fallback(prompt)
    return {
        "response": extract_text(result.content),
        "messages": [result],
    }


def route_by_approval(state: State) -> str:
    """Routes to end if approved, or back to feedback loop if rejected."""
    if state["approved"]:
        return "return_response"
    return "human_feedback"