from memory.mongodb import get_mongo_connection_string


def test_mongo_tls(monkeypatch):
    monkeypatch.setattr("memory.mongodb.settings.MONGO_HOST", "localhost")
    monkeypatch.setattr("memory.mongodb.settings.MONGO_PORT", 27017)
    monkeypatch.setattr("memory.mongodb.settings.MONGO_TLS", True)
    monkeypatch.setattr("memory.mongodb.settings.MONGO_USER", None)
    monkeypatch.setattr("memory.mongodb.settings.MONGO_PASSWORD", None)
    monkeypatch.setattr("memory.mongodb.settings.MONGO_AUTH_SOURCE", None)
    assert "tls=true" in get_mongo_connection_string()
