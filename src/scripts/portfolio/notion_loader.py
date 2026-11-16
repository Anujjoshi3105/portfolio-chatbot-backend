import os
import traceback

from langchain_community.document_loaders import NotionDBLoader
from langchain_core.documents import Document

NOTION_DB_MAP = {
    "education": "NOTION_EDUCATION_ID",
    "experience": "NOTION_EXPERIENCE_ID",
    "projects": "NOTION_PROJECT_ID",
    "testimonials": "NOTION_TESTIMONIAL_ID",
    "blog": "NOTION_BLOG_ID",
}


class NotionLoader:
    """Service for loading documents from Notion databases."""

    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        if not self.token:
            print("WARNING: NOTION_TOKEN not found in environment")

    def load_category(self, category: str, since_date: str | None = None) -> list[Document]:
        """
        Loads documents from a Notion database for a given category.

        Args:
            category: The category name (must be in NOTION_DB_MAP)
            since_date: Optional ISO 8601 date to filter documents updated after this date

        Returns:
            List of documents that were updated after since_date
        """
        if category not in NOTION_DB_MAP:
            print(f"WARNING: Unknown category: {category}")
            return []

        env_key = NOTION_DB_MAP[category]
        db_id = os.getenv(env_key)

        if not db_id:
            print(f"WARNING: Notion database ID not found for category: {category}")
            return []

        if not self.token:
            print("ERROR: NOTION_TOKEN not available")
            return []

        try:
            print(f"INFO: Loading {category} documents from Notion...")
            loader = NotionDBLoader(self.token, db_id)
            all_docs = loader.load()

            if since_date:
                valid_docs = [d for d in all_docs if d.metadata.get("updated", "") > since_date]
                print(
                    f"INFO: Found {len(valid_docs)} documents updated after {since_date} out of {len(all_docs)} total"
                )
            else:
                valid_docs = all_docs
                print(f"INFO: Loaded {len(valid_docs)} documents (no date filter)")

            return valid_docs
        except Exception as e:
            print(f"ERROR: Failed to load {category} from Notion: {e}")
            traceback.print_exc()
            return []
