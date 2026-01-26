import json
import hashlib
import time
import re
from typing import Optional, List, Tuple

from langsmith import uuid7
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.llm import get_model
from core.settings import settings
from scripts.portfolio.prompt import PORTFOLIO_INGESTION_SYSTEM_PROMPT

class DocumentChunker:
    """Service for splitting documents into chunks."""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            is_separator_regex=True,
        )
        print(f"DEBUG: Initialized DocumentChunker with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def chunk_document(self, doc: Document, base_id: str, content_hash: str) -> List[Tuple[Document, str]]:
        """
        Splits a document into chunks and prepares them for storage.
        
        Args:
            doc: The document to chunk
            base_id: The base document ID
            content_hash: The content hash for change detection
            
        Returns:
            List of tuples (chunk_document, chunk_id)
        """
        chunks = self.text_splitter.split_documents([doc])
        chunked_docs = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{base_id}_chunk_{idx}"
            chunk.metadata["content_hash"] = content_hash
            chunk.metadata["base_id"] = base_id
            chunked_docs.append((chunk, chunk_id))
        
        print(f"DEBUG: Split document {base_id} into {len(chunked_docs)} chunks")
        return chunked_docs


class DocumentEnricher:
    """Service for enriching documents using LLM with generalized retry logic."""
    
    def __init__(self):
        self.llm = get_model(settings.DEFAULT_MODEL)
        self.enrich_prompt = ChatPromptTemplate.from_messages([
            ("system", PORTFOLIO_INGESTION_SYSTEM_PROMPT),
            ("human", "Category: {category}\n\nMetadata:\n{metadata}\n\nContent:\n{content}")
        ])
        print(f"INFO: Initialized DocumentEnricher with {settings.DEFAULT_MODEL}")
    
    def enrich(self, doc: Document, category: str, max_retries: int = 5) -> Tuple[Optional[Document], str, str]:
        pid = str(doc.metadata.get("id", uuid7()))
        title = doc.metadata.get("Title", "Untitled")
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = min(2 ** attempt, 60)
                    print(f"INFO: Retrying {title} (attempt {attempt + 1}/{max_retries}) in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"INFO: Enriching document: {title} (PID: {pid})")
                
                res = self.llm.invoke(
                    self.enrich_prompt.format_messages(
                        category=category,
                        metadata=json.dumps(doc.metadata, default=str),
                        content=doc.page_content or "No content provided."
                    ),
                    config=RunnableConfig(run_id=uuid7())
                )
                
                enriched_content = res.content.strip()
                content_hash = hashlib.sha256(enriched_content.encode('utf-8')).hexdigest()
                
                enriched_doc = Document(
                    page_content=enriched_content,
                    metadata={
                        **doc.metadata,
                        "category": category,
                        "content_hash": content_hash,
                        "base_id": pid
                    }
                )
                return enriched_doc, pid, content_hash
                
            except Exception as e:
                error_msg = str(e).lower()
                error_type = type(e).__name__.lower()
                
                # --- Rate Limit Detection ---
                is_rate_limit = any(keyword in error_msg or keyword in error_type 
                                   for keyword in ["429", "rate_limit", "rate limit", "too many requests", "throttled"])
                
                # --- Overloaded/Server Error Detection ---
                is_server_error = any(keyword in error_msg 
                                     for keyword in ["500", "502", "503", "overloaded", "unavailable", "deadline_exceeded"])

                if is_rate_limit or is_server_error:
                    wait_time = 5 # Default
                    match = re.search(r'(?:try again in|retry after|wait)\s*([\d.]+)\s*s', error_msg)
                    if match:
                        wait_time = float(match.group(1)) + 1
                    
                    if attempt < max_retries - 1:
                        print(f"WARN: API issue (Rate Limit/Overload) for {title}. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Non-retriable or final attempt failure
                print(f"ERROR: Enrichment failed for {title}: {e}")
                if attempt >= 1:
                    return None, pid, ""

        return None, pid, ""