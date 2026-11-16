import json

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from core.utils import convert_tool_response_to_toon
from memory.postgres import load_pgvector_retriever


class DatabaseSearchInput(BaseModel):
    """Input for database search."""

    query: str = Field(
        description="The natural language search query to look up information from Anuj's portfolio."
    )


@tool("Database_Search", args_schema=DatabaseSearchInput)
def database_search(query: str) -> str:
    """Search for relevant information about Anuj Joshi's education, experience, projects, blog posts, testimonials, and skills.

    This tool should be used whenever the user asks about Anuj's background, work, or specific accomplishments.
    """

    retriever = load_pgvector_retriever(4)
    documents = retriever.invoke(query)

    if not documents:
        return "No relevant portfolio information found."

    formatted_docs = []

    for i, doc in enumerate(documents):
        docs = {"content": doc.page_content, "metadata": doc.metadata}
        formatted_docs.append(convert_tool_response_to_toon(json.dumps(docs)))

    return "\n\n".join(formatted_docs)
