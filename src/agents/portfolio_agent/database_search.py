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
        metadata = doc.metadata
        content = doc.page_content.strip()

        formatted_docs.append(
            f"--- Document {i + 1} ({metadata}) ---\n{content}"
        )

    return "\n\n".join(formatted_docs)


# DATABASE SEARCH TOOL
def database_search_func(query: str) -> str:
    """
    Use this tool to search for relevant information about Anuj Joshi's education, experience, projects, blog posts, testimonials, skills, etc.
    """

    documents = hybrid_search(query, k=6)

    if not documents:
        return "No relevant portfolio information found."

    return format_contexts(documents)


database_search: BaseTool = tool(database_search_func)
database_search.name = "Database_Search"
