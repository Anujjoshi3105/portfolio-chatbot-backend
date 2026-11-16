from agents import get_all_agent_info


def test_all_planned_agent_categories_are_registered():
    keys = {item.key for item in get_all_agent_info()}
    assert {"supervisor-agent", "contact-agent", "background-agent", "github-mcp-agent"} <= keys
