"""
Graph.py
--------
Builds and compiles the full LangGraph workflow for the project.

Flow (matches the architecture diagram):

    Query_Optimizer_Model
            |
            v
    Query_Classification_Model
            |
      (route_by_query_intent)
            |
      +-----+-----+
document_loader   general_question --> END
      |
      v
Context_Evaluation_Model
      |
(route_by_context_sufficiency)
      |
  +---+-----------------------------+
query_optimizer (loop)   [citation_model, metadata_model, prompt_builder_model]  <- parallel
                                      |
                                Merge_Context
                                      |
                          Response_Generation_Model
                                      |
                              Human_Review_Node   <- interrupt() pauses here
                                      |
                            (route_by_approval)
                                      |
                        +-------------+-------------+
                    APPROVED                    REJECTED
                        |                             |
                       END                Human_Feedback_Model
                                                        |
                                              Human_Review_Node (loop)
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import State
from Nodes import (
    Query_Optimizer_Model,
    Query_Classification_Model,
    Document_Loader,
    Context_Evaluation_Model,
    General_Question,
    Response_Generation_Model,
    route_by_query_intent,
    route_by_context_sufficiency,
    Citation_Model,
    Metadata_Model,
    Prompt_Builder_Model,
    Merge_Context,
    Human_Review_Node,
    Human_Feedback_Model,
    route_by_approval,
)


def build_graph():
    # ---- Initialize the graph with our shared State schema ----
    builder = StateGraph(State)

    # =====================================================
    # Register all nodes (name -> function)
    # =====================================================
    builder.add_node("query_optimizer", Query_Optimizer_Model)
    builder.add_node("query_classification", Query_Classification_Model)
    builder.add_node("document_loader", Document_Loader)
    builder.add_node("context_evaluation", Context_Evaluation_Model)
    builder.add_node("general_question", General_Question)

    # Parallel processing nodes (run simultaneously)
    builder.add_node("citation_model", Citation_Model)
    builder.add_node("metadata_model", Metadata_Model)
    builder.add_node("prompt_builder_model", Prompt_Builder_Model)
    builder.add_node("merge_context", Merge_Context)

    builder.add_node("response_generation", Response_Generation_Model)

    # Human-in-the-loop nodes
    builder.add_node("human_review", Human_Review_Node)
    builder.add_node("human_feedback", Human_Feedback_Model)

    # =====================================================
    # Entry point — every request starts by optimizing the query
    # =====================================================
    builder.add_edge(START, "query_optimizer")
    builder.add_edge("query_optimizer", "query_classification")

    # =====================================================
    # Conditional routing #1 — document vs general question
    # =====================================================
    builder.add_conditional_edges(
        "query_classification",
        route_by_query_intent,
        {
            "document_loader": "document_loader",
            "general_question": "general_question",
        },
    )

    # General questions skip the whole RAG pipeline and end immediately
    builder.add_edge("general_question", END)

    # =====================================================
    # Iterative retrieval loop (Context_Evaluation_Model)
    # =====================================================
    builder.add_edge("document_loader", "context_evaluation")

    # If context is insufficient -> loop back to query_optimizer
    # If sufficient (or retry limit hit) -> fan out to the 3 parallel nodes
    builder.add_conditional_edges(
        "context_evaluation",
        route_by_context_sufficiency,
        {
            "query_optimizer": "query_optimizer",          # loop
            "citation_model": "citation_model",             # fan-out branch 1
            "metadata_model": "metadata_model",              # fan-out branch 2
            "prompt_builder_model": "prompt_builder_model",  # fan-out branch 3
        },
    )

    # =====================================================
    # Parallel processing — all 3 nodes feed into merge_context
    # =====================================================
    builder.add_edge("citation_model", "merge_context")
    builder.add_edge("metadata_model", "merge_context")
    builder.add_edge("prompt_builder_model", "merge_context")

    # Once merged, generate the final response
    builder.add_edge("merge_context", "response_generation")

    # =====================================================
    # Human-in-the-loop review
    # =====================================================
    builder.add_edge("response_generation", "human_review")

    builder.add_conditional_edges(
        "human_review",
        route_by_approval,
        {
            "return_response": END,
            "human_feedback": "human_feedback",
        },
    )

    # Rejected responses go through feedback, then back for another review
    builder.add_edge("human_feedback", "human_review")

    # =====================================================
    # Compile with a checkpointer — required for interrupt()/human_review
    # to pause and resume correctly
    # =====================================================
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


# Ready-to-use compiled graph
graph = build_graph()