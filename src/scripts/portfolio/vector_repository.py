from sqlalchemy import text

from core.settings import settings
from memory.postgres import load_pgvector_store


class VectorRepository:
    """Repository for querying and managing vector store data."""

    def __init__(self):
        self.store = load_pgvector_store()
        self.collection_name = settings.VECTOR_STORE_COLLECTION_NAME

    def get_existing_chunks(self, base_id: str) -> list[str]:
        """
        Retrieves all chunk IDs for a given base document ID.

        Args:
            base_id: The base document ID

        Returns:
            List of chunk UUIDs as strings
        """
        query = text("""
            SELECT e.id::text
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = :cname 
            AND (e.cmetadata->>'base_id' = :base_id OR e.id::text LIKE :pattern)
        """)
        try:
            with self.store._engine.connect() as conn:
                results = conn.execute(
                    query,
                    {
                        "cname": self.collection_name,
                        "base_id": base_id,
                        "pattern": f"{base_id}_chunk_%",
                    },
                ).fetchall()
                return [row[0] for row in results if row[0]]
        except Exception as e:
            print(f"WARNING: Could not fetch existing chunks for {base_id}: {e}")
            return []

    def get_existing_content_hash(self, base_id: str) -> str | None:
        """
        Retrieves the content hash for a given base document ID from the first chunk's metadata.

        Args:
            base_id: The base document ID

        Returns:
            Content hash string or None if not found
        """
        query = text("""
            SELECT e.cmetadata->>'content_hash'
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = :cname 
            AND (e.cmetadata->>'base_id' = :base_id OR e.id::text LIKE :pattern)
            LIMIT 1
        """)
        try:
            with self.store._engine.connect() as conn:
                result = conn.execute(
                    query,
                    {
                        "cname": self.collection_name,
                        "base_id": base_id,
                        "pattern": f"{base_id}_chunk_%",
                    },
                ).fetchone()
                return result[0] if result and result[0] else None
        except Exception as e:
            print(f"WARNING: Could not fetch content hash for {base_id}: {e}")
            return None

    def batch_get_existing_content_hashes(self, base_ids: list[str]) -> dict[str, str | None]:
        """
        Batch fetches content hashes for multiple base document IDs in a single query.

        Args:
            base_ids: List of base document IDs

        Returns:
            Dictionary mapping base_id -> content_hash (or None if not found)
        """
        if not base_ids:
            return {}

        query = text("""
            SELECT DISTINCT ON (base_id) base_id, content_hash
            FROM (
                SELECT 
                    e.cmetadata->>'base_id' as base_id,
                    e.cmetadata->>'content_hash' as content_hash
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = :cname
                AND e.cmetadata->>'base_id' = ANY(:base_ids)
            ) subq
            WHERE base_id = ANY(:base_ids)
            ORDER BY base_id
        """)

        try:
            with self.store._engine.connect() as conn:
                results = conn.execute(
                    query, {"cname": self.collection_name, "base_ids": base_ids}
                ).fetchall()

                hash_map = {base_id: None for base_id in base_ids}
                for row in results:
                    if row[0] and row[1]:  # base_id and content_hash both present
                        hash_map[row[0]] = row[1]

                return hash_map
        except Exception as e:
            print(f"WARNING: Could not batch fetch content hashes: {e}")
            return {base_id: None for base_id in base_ids}

    def get_last_sync_date(self) -> str:
        """
        Fetches the most recent 'updated' timestamp from the vector store.

        Returns:
            ISO 8601 timestamp string or default epoch date if none found
        """
        query = text("""
            SELECT e.cmetadata->>'updated' 
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = :cname
            ORDER BY e.cmetadata->>'updated' DESC LIMIT 1
        """)
        try:
            with self.store._engine.connect() as conn:
                result = conn.execute(query, {"cname": self.collection_name}).fetchone()
                return result[0] if result else "1970-01-01T00:00:00.000Z"
        except Exception as e:
            print(f"WARNING: Could not fetch last sync date: {e}")
            return "1970-01-01T00:00:00.000Z"
