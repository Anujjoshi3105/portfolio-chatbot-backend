import json
import logging

import toons

logger = logging.getLogger(__name__)


def convert_tool_response_to_toon(content: str) -> str:
    """
    Convert JSON tool response to TOON format to reduce tokens (30–60% fewer than JSON).
    https://pypi.org/project/toons/
    """
    if not content or not isinstance(content, str):
        return content
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return content
    try:
        return toons.dumps(data)
    except Exception as e:
        logger.warning("Failed to encode TOON, returning raw content: %s", e)
        return content
