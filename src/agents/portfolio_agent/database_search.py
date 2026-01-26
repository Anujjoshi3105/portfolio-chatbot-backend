from typing import List

from langchain_core.documents import Document
from langchain_core.tools import BaseTool, tool
from memory.postgres import load_pgvector_retriever


def hybrid_search(query: str, k: int = 6) -> List[Document]:
    retriever = load_pgvector_retriever(k)
    return retriever.invoke(query)


def format_contexts(documents: List[Document]) -> str:
    formatted_docs = []

    for i, doc in enumerate(documents):
        source = doc.metadata.get("source_db", "Unknown")
        content = doc.page_content.strip()

        formatted_docs.append(
            f"--- Document {i + 1} (Source: {source}) ---\n{content}"
        )

    return "\n\n".join(formatted_docs)


# DATABASE SEARCH TOOL
def database_search_func(query: str) -> str:
    """
    Search Anuj Joshi's portfolio database for any information.
    Use this tool whenever the user asks about education, experience, projects, blog posts, testimonials, or any other information NOT available 
    in your system prompt.
    """

    documents = hybrid_search(query, k=6)

    if not documents:
        return "No relevant portfolio information found."

    return format_contexts(documents)


database_search: BaseTool = tool(database_search_func)
database_search.name = "Database_Search"
