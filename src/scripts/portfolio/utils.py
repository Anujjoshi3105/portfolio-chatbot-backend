import re

import yaml

FRONTMATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


def extract_metadata_and_content(text: str):
    """
    Extracts metadata and content from a string containing frontmatter.
    """
    match = FRONTMATTER_REGEX.match(text)
    if not match:
        return {}, text

    try:
        metadata = yaml.safe_load(match.group(1)) or {}
        if isinstance(metadata, dict):
            return metadata, match.group(2)
    except Exception:
        pass

    return {}, text


def process_document(doc):
    """
    Handles metadata extraction and content cleaning for a single document object.
    """
    metadata, body = extract_metadata_and_content(doc.page_content)
    doc.page_content = body
    new_metadata = {}
    if "url" in metadata:
        new_metadata["source"] = metadata["url"]

    for k, v in metadata.items():
        if k != "url":
            new_metadata[k] = v

    doc.metadata = new_metadata
    return doc
