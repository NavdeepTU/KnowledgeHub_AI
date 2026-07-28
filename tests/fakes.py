"""Shared test doubles, kept separate from conftest.py so they can be
imported directly by tests that want to construct them explicitly."""


def fake_encoder(texts: list[str]) -> list[list[float]]:
    """Stands in for a real sentence-transformers model - no model
    download, no multi-second load time, deterministic output."""
    return [[0.1, 0.2, 0.3] for _ in texts]
