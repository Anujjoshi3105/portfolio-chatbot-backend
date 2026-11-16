from client.client import AgentClient


def test_client_parses_done_and_tokens(monkeypatch):
    client = AgentClient(get_info=False, base_url="http://test")
    assert client._parse_stream_line('data: {"type": "token", "content": "hi"}') == "hi"
    assert client._parse_stream_line("data: [DONE]") is None
