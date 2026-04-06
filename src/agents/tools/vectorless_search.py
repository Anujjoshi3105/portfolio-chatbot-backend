import json
from pydantic import BaseModel, Field
import logging

from langchain_core.tools import BaseTool, tool
from langchain_core.prompts import PromptTemplate
from core import get_model, settings

from scripts.portfolio.notion_loader import NotionLoader

logger = logging.getLogger(__name__)


class VectorlessSearchInput(BaseModel):
    """Input for vectorless search."""
    category: str = Field(description="The category of portfolio data to search (education, experience, projects, testimonials, blog).")
    query: str = Field(description="The specific question the user asked or the information needed.")


@tool("Vectorless_Search", args_schema=VectorlessSearchInput)
def vectorless_search(category: str, query: str) -> str:
    """Read full documents directly from Notion statelessly, and use an LLM to select the most relevant ones.
    
    This replaces traditional vector databases by using real-time LLM reasoning to identify which files contain the necessary information.
    """
    try:
        loader = NotionLoader()
        docs = loader.load_category(category)
        
        if not docs:
            return f"No documents found for category: {category}."
            
        # Step 1: Smart Document Selection (Vectorless approach)
        # Create a rich index for the LLM to review
        doc_index = []
        for i, doc in enumerate(docs):
            meta_str = ", ".join(f"{k}: {v}" for k, v in doc.metadata.items() if isinstance(v, (str, int, float)) and len(str(v)) < 100)
            snippet = doc.page_content[:300].replace('\n', ' ')
            doc_index.append(f"[{i}] Metadata: {meta_str} | Content: {snippet}...")
            
        index_str = "\n".join(doc_index)
        
        # Determine relevant indices using a fast, cheap LLM call
        selection_prompt = PromptTemplate.from_template(
            "You are a vectorless document selection agent.\n"
            "Given the user's query and a list of available documents (Format: [ID] Metadata | Content),\n"
            "identify which document IDs are most likely to contain the answer.\n"
            "Return ONLY a comma-separated list of integer IDs (e.g., 0,3,5), or 'NONE' if none are relevant.\n"
            "If all documents seem potentially relevant or you are unsure, return 'ALL'.\n\n"
            "Query: {query}\n\nDocuments:\n{index_str}"
        )
        
        # We can use the default model for selection
        llm = get_model(settings.DEFAULT_MODEL)
        selection_chain = selection_prompt | llm
        
        selection_result = selection_chain.invoke({"query": query, "index_str": index_str})
        result_text = selection_result.content.strip()
        
        if result_text.upper() == "NONE" or not result_text:
            return "No relevant portfolio information found in the retrieved documents."
            
        # Parse the IDs
        selected_indices = []
        if "ALL" in result_text.upper():
            selected_indices = list(range(len(docs)))
        else:
            import re
            numbers = re.findall(r'\d+', result_text)
            for id_str in numbers:
                try:
                    selected_indices.append(int(id_str))
                except ValueError:
                    continue
                
        # Step 2: Extract Relevant Pages/Chunks
        formatted_docs = []
        for i in selected_indices:
            if 0 <= i < len(docs):
                doc = docs[i]
                data = {"content": doc.page_content, "metadata": doc.metadata}
                formatted_docs.append(json.dumps(data))
                
        if not formatted_docs:
            return "Failed to extract relevant documents based on selection."
            
        # Return the extracted raw text to the main agent for Step 3: Answer Generation
        return "\n\n---\n\n".join(formatted_docs)
        
    except Exception as e:
        logger.error(f"Error in vectorless_search: {e}")
        return f"Error executing vectorless search: {e}"
