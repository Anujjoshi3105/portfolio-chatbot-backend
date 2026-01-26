import requests
from core import settings
from langchain_core.tools import BaseTool, tool


def get_contest_ratings(username: str = "anujjoshi3105") -> str:
    """
    Use this tool to get the latest contest ratings and statistics for Anuj Joshi from various competitive programming platforms.    
    This tool fetches real-time data from Codeforces, CodeChef, LeetCode, and GeeksforGeeks.
    
    Args:
        username: The username to fetch ratings for (default: anujjoshi3105)
    
    Returns:
        A formatted string with contest ratings and statistics from all platforms.
    """
    try:
        if settings.CONTEST_API_URL is None:
            return "Error: Contest API URL is not set"
        url = f"{settings.CONTEST_API_URL}?username={username}"
        response = requests.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error fetching contest ratings: {str(e)}"


contest_ratings: BaseTool = tool(get_contest_ratings)
contest_ratings.name = "Contest_Ratings"