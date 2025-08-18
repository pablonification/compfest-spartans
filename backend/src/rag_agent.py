"""
SmartBin AI Agent – RAG app bootstrap

Builds a simple Retrieval-Augmented Generation pipeline over the provided
markdown knowledge base, exposing an `app.invoke({"messages": [...]}, config)
API that returns a state containing the conversation messages. Designed to be
imported by FastAPI router at backend/src/backend/routers/rag.py
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI


KB_FILE_NAME = "Markdown For RAG 25235539e3b580e39241d3dddf194c64.md"
KB_PATHS = [
    Path("/app/docs") / KB_FILE_NAME,  # container path (docker-compose mounts ./docs)
    Path(__file__).resolve().parents[2] / "docs" / KB_FILE_NAME,  # local dev
]


def _load_kb_text() -> str:
    for p in KB_PATHS:
        if p.exists():
            return p.read_text(encoding="utf-8")
    # Fallback to empty if not found
    return ""


def _build_retriever() -> Chroma:
    kb_text = _load_kb_text()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    docs = splitter.create_documents([kb_text]) if kb_text else []

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vs = Chroma.from_documents(docs, embeddings, collection_name="smartbin_rag")
    return vs.as_retriever(search_kwargs={"k": 4})


SYSTEM_PROMPT = (
    "You are SmartBin AI Agent, an expert assistant for recycling and waste management.\n"
    "Use only the provided context to answer in clear, concise Bahasa Indonesia,\n"
    "with brief actionable guidance. If the answer is not in the context, say\n"
    "you don't know and suggest relevant steps. Prefer concrete numbers, simple\n"
    "lists, and short paragraphs. Avoid speculation.\n\n"
    "Rules:\n"
    "- Focus on botol plastik, PET, 3R/5R, dan kebijakan/angka yang ada di konteks.\n"
    "- Jika pertanyaan tentang fitur SmartBin, jelaskan sesuai ringkasan produk.\n"
    "- Beri saran praktis (cara memilah, bersihkan botol, dll.) bila relevan.\n"
    "- Jangan mengada-ada di luar konteks.\n"
)


class SimpleRAGApp:
    def __init__(self) -> None:
        self.retriever = _build_retriever()
        # Gemini 2.0 Flash (or fallback if env not set)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

    def invoke(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        messages: List[Any] = state.get("messages", [])
        # Find last human query
        user_query = None
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                user_query = m.content
                break
            if isinstance(m, dict) and m.get("type") == "human":
                user_query = m.get("content")
                break

        if not user_query:
            user_query = "Jelaskan ringkas tentang SmartBin dan 3R."

        # Retrieve context
        contexts = []
        try:
            docs = self.retriever.get_relevant_documents(user_query)
            contexts = [d.page_content for d in docs]
        except Exception:
            contexts = []

        context_block = "\n\n".join(contexts[:4]) if contexts else ""
        prompt = (
            "Konteks berikut berasal dari dokumen internal SmartBin. Gunakan seperlunya.\n\n"
            f"{context_block}\n\n"
            f"Pertanyaan: {user_query}\n"
            "Jawab singkat, jelas, dan actionable."
        )

        # Call LLM
        ai_msg = self.llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        # Return message list as expected
        out_messages = list(messages) + [AIMessage(content=getattr(ai_msg, "content", str(ai_msg)))]
        return {"messages": out_messages}


# Public app instance
app = SimpleRAGApp()
