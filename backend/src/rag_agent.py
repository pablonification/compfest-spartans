"""
Agentic RAG workflow backed by LangGraph, powered by Google Gemini 2.0 Flash,
retrieving knowledge from the SmartBin markdown documentation.

Usage:
    export GOOGLE_API_KEY=...
    python -m backend.src.rag_agent

This will run a quick demo query. Integrate the `app` object in your FastAPI
or other orchestration as needed.
"""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

# ---------------------------------------------------------------------------
# Knowledge base configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC_PATHS = [
    os.path.join(
        BASE_DIR,
        "docs",
        "Markdown For RAG 25235539e3b580e39241d3dddf194c64.md",
    ),
    os.path.join(
        BASE_DIR,
        "docs",
        "Markdown for RAG 2 25235539e3b580ab9f49dc089ed98622.md",
    ),
]


def _build_retriever():
    """Create a persistent retriever over the markdown knowledge base."""

    loaders = [TextLoader(path) for path in DOC_PATHS]
    docs = []
    for loader in loaders:
        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=120)
    chunks = splitter.split_documents(docs)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        collection_name="smartbin_kb",
        embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
    )

    return vectorstore.as_retriever()


# Build once at import time to avoid repeated work
_RETRIEVER = _build_retriever()


# ---------------------------------------------------------------------------
# Tool definition (retrieval)
# ---------------------------------------------------------------------------


@tool
def retrieve_context(query: str) -> str:  # noqa: D401
    """Search SmartBin KB for relevant context."""
    results = _RETRIEVER.invoke(query)
    return "\n".join(doc.page_content for doc in results)


# ---------------------------------------------------------------------------
# LLM + LangGraph orchestration
# ---------------------------------------------------------------------------

TOOLS = [retrieve_context]
TOOL_NODE = ToolNode(TOOLS)

# Gemini 2.0 Flash (via LangChain wrapper)
MODEL = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0).bind_tools(TOOLS)


def _should_continue(state: MessagesState) -> Literal["tools", END]:
    last = state["messages"][-1]
    # If the LLM decided to call a tool, route to the tool node
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def _call_model(state: MessagesState):
    response = MODEL.invoke(state["messages"])
    return {"messages": [response]}


# Assemble the workflow
GRAPH = StateGraph(MessagesState)
GRAPH.add_node("agent", _call_model)
GRAPH.add_node("tools", TOOL_NODE)
GRAPH.add_edge(START, "agent")
GRAPH.add_conditional_edges("agent", _should_continue)
GRAPH.add_edge("tools", "agent")

app = GRAPH.compile()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "GOOGLE_API_KEY" not in os.environ:
        raise EnvironmentError("Please set the GOOGLE_API_KEY environment variable")

    query = "Jelaskan hierarki pengelolaan sampah 3R dan 5R"
    final_state = app.invoke({"messages": [HumanMessage(content=query)]})
    print("\n=== Answer ===\n")
    print(final_state["messages"][-1].content)
