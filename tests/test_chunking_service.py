import pytest

from app.services.chunking_service import ChunkingService


@pytest.fixture()
def chunking_service() -> ChunkingService:
    return ChunkingService()


def test_chunk_text_returns_empty_list_for_empty_text(
    chunking_service: ChunkingService,
) -> None:
    assert chunking_service.chunk_text("", chunk_size=100, overlap=20) == []


def test_chunk_text_returns_single_chunk_when_shorter_than_chunk_size(
    chunking_service: ChunkingService,
) -> None:
    text = "short text"

    chunks = chunking_service.chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == text
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == len(text)
    assert chunks[0].character_count == len(text)


def test_chunk_text_splits_long_text_with_overlap(
    chunking_service: ChunkingService,
) -> None:
    text = "a" * 2500

    chunks = chunking_service.chunk_text(text, chunk_size=1000, overlap=200)

    assert len(chunks) == 3
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    # Every chunk after the first should start exactly `overlap` characters
    # before the previous chunk ended.
    assert chunks[1].start_offset == chunks[0].end_offset - 200
    assert chunks[2].start_offset == chunks[1].end_offset - 200
    # The whole text should be covered, with the last chunk ending exactly
    # at the end of the text.
    assert chunks[-1].end_offset == len(text)


def test_chunk_text_covers_every_character_with_no_gaps(
    chunking_service: ChunkingService,
) -> None:
    text = "".join(str(i % 10) for i in range(2500))

    chunks = chunking_service.chunk_text(text, chunk_size=1000, overlap=200)

    reconstructed = chunks[0].text
    for previous, current in zip(chunks, chunks[1:]):
        overlap_len = previous.end_offset - current.start_offset
        reconstructed += current.text[overlap_len:]

    assert reconstructed == text


def test_chunk_text_rejects_overlap_not_smaller_than_chunk_size(
    chunking_service: ChunkingService,
) -> None:
    with pytest.raises(ValueError, match="overlap"):
        chunking_service.chunk_text("some text", chunk_size=100, overlap=100)
