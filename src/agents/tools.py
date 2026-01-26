import re
import math
import numexpr

from memory.postgres import load_pgvector_retriever
from langchain_core.tools import BaseTool, tool


def calculator_func(expression: str) -> str:
    """Calculates a math expression using numexpr.

    Useful for when you need to answer questions about math using numexpr.
    This tool is only for math questions and nothing else. Only input
    math expressions.

    Args:
        expression (str): A valid numexpr formatted math expression.

    Returns:
        str: The result of the math expression.
    """

    try:
        local_dict = {"pi": math.pi, "e": math.e}
        output = str(
            numexpr.evaluate(
                expression.strip(),
                global_dict={},  # restrict access to globals
                local_dict=local_dict,  # add common mathematical functions
            )
        )
        return re.sub(r"^\[|\]$", "", output)
    except Exception as e:
        raise ValueError(
            f'calculator("{expression}") raised error: {e}.'
            " Please try again with a valid numerical expression"
        )


calculator: BaseTool = tool(calculator_func)
calculator.name = "Calculator"

def format_contexts(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def database_search_func(query: str) -> str:
    """Searches the vector DB for information in the portfolio."""
    retriever = load_pgvector_retriever()
    documents = retriever.invoke(query)
    context_str = format_contexts(documents)

    return context_str


database_search: BaseTool = tool(database_search_func)
database_search.name = "Database_Search"
