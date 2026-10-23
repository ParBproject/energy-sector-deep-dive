import pytest


@pytest.fixture(autouse=True)
def isolated_raw_dir(tmp_path, monkeypatch):
    """Never touch the real data/raw or the network-backed env during tests."""
    monkeypatch.setenv("ESD_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    monkeypatch.delenv("RIG_COUNT_FILE", raising=False)
    return tmp_path / "raw"


class FakeResponse:
    def __init__(self, text="", payload=None, status=200):
        self.text, self._payload, self.status_code = text, payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload
