import traceback

from langchain_community.vectorstores.utils import filter_complex_metadata

from core.settings import settings
from memory.postgres import load_pgvector_store
from scripts.portfolio.document import DocumentChunker, DocumentEnricher
from scripts.portfolio.notion_loader import NotionLoader
from scripts.portfolio.vector_repository import VectorRepository

NOTION_DB_MAP = {
    "education": "NOTION_EDUCATION_ID",
    "experience": "NOTION_EXPERIENCE_ID",
    "projects": "NOTION_PROJECT_ID",
    "testimonials": "NOTION_TESTIMONIAL_ID",
    "blog": "NOTION_BLOG_ID",
}


class PortfolioIngest:
    """Orchestrates the portfolio synchronization process."""

    def __init__(self):
        self.enricher = DocumentEnricher()
        self.chunker = DocumentChunker()
        self.loader = NotionLoader()
        self.repository = VectorRepository()
        self.store = load_pgvector_store()
        print(
            f"INFO: Initialized PortfolioIngest with collection: {settings.VECTOR_STORE_COLLECTION_NAME}"
        )

    def ingest_category(self, category: str, since_date: str) -> tuple[int, int, int, int]:
        """
        Synchronizes a single category of documents.

        Args:
            category: The category to sync
            since_date: ISO 8601 date to filter documents

        Returns:
            Tuple of (chunks_deleted, chunks_updated, chunks_skipped, total_synced)
        """
        # Load documents from Notion
        valid_docs = self.loader.load_category(category, since_date)
        if not valid_docs:
            print(f"INFO: No new updates for {category}")
            return 0, 0, 0, 0

        # Enrich documents with LLM sequentially to avoid rate limits
        print(f"INFO: Enriching {len(valid_docs)} documents with LLM...")

        enriched_docs = []
        base_ids = []
        content_hashes = []

        for doc in valid_docs:
            enriched_doc, base_id, content_hash = self.enricher.enrich(doc, category)
            if enriched_doc is not None:
                enriched_docs.append(enriched_doc)
                base_ids.append(base_id)
                content_hashes.append(content_hash)

        if not enriched_docs:
            print(f"INFO: No enriched documents for {category}")
            return 0, 0, 0, 0

        # Batch fetch existing content hashes
        print(f"INFO: Checking content hashes for {len(enriched_docs)} documents...")
        existing_hashes = self.repository.batch_get_existing_content_hashes(base_ids)
        print(
            f"DEBUG: Found {len([h for h in existing_hashes.values() if h is not None])} existing hashes"
        )

        # Process documents and prepare for upsert
        docs_to_upsert = []
        ids_to_upsert = []
        chunks_deleted = 0
        chunks_updated = 0
        chunks_skipped = 0

        for enriched_doc, base_id, new_hash in zip(enriched_docs, base_ids, content_hashes):
            existing_hash = existing_hashes.get(base_id)

            if existing_hash is None:
                # New document
                print(f"INFO: New document {base_id}, adding all chunks...")
                chunked = self.chunker.chunk_document(enriched_doc, base_id, new_hash)
                for chunk, chunk_id in chunked:
                    docs_to_upsert.append(chunk)
                    ids_to_upsert.append(chunk_id)
                chunks_updated += len(chunked)
            elif existing_hash != new_hash:
                # Content changed
                print(f"INFO: Content changed for {base_id}, replacing chunks...")
                old_chunk_ids = self.repository.get_existing_chunks(base_id)
                if old_chunk_ids:
                    self.store.delete(old_chunk_ids)
                    chunks_deleted += len(old_chunk_ids)
                    print(f"DEBUG: Deleted {len(old_chunk_ids)} old chunks for {base_id}")

                chunked = self.chunker.chunk_document(enriched_doc, base_id, new_hash)
                for chunk, chunk_id in chunked:
                    docs_to_upsert.append(chunk)
                    ids_to_upsert.append(chunk_id)
                chunks_updated += len(chunked)
            else:
                # Content unchanged
                print(f"DEBUG: Content unchanged for {base_id}, skipping...")
                chunks_skipped += 1

        # Upsert documents
        total_synced = 0
        if docs_to_upsert:
            print(f"INFO: Upserting {len(docs_to_upsert)} chunks...")
            self.store.add_documents(filter_complex_metadata(docs_to_upsert), ids=ids_to_upsert)
            total_synced = len(docs_to_upsert)
            print(
                f"INFO: Category {category}: Deleted {chunks_deleted} chunks, "
                f"updated {chunks_updated} chunks, skipped {chunks_skipped} unchanged documents, "
                f"total synced: {total_synced}"
            )

        return chunks_deleted, chunks_updated, chunks_skipped, total_synced

    def sync(self, manual_date: str | None = None) -> int:
        """
        Synchronizes all portfolio categories.

        Args:
            manual_date: Optional ISO 8601 date to override last sync date

        Returns:
            Total number of chunks synced
        """
        since_date = manual_date or self.repository.get_last_sync_date()
        print(f"INFO: Starting sync for items modified after: {since_date}")

        total_synced = 0

        for category in NOTION_DB_MAP.keys():
            try:
                chunks_deleted, chunks_updated, chunks_skipped, synced = self.ingest_category(
                    category, since_date
                )
                total_synced += synced
            except Exception as e:
                print(f"ERROR: Failed to sync category {category}: {e}")
                traceback.print_exc()

        print(f"INFO: Sync complete. Total chunks synced: {total_synced}")
        return total_synced
