from pathlib import Path

import pytest

from app.schemas.document import ConversationTurn
from app.services.conversation_service import ConversationService


@pytest.fixture()
def conversation_service(tmp_path: Path) -> ConversationService:
    return ConversationService(storage_directory=tmp_path / "conversations")


def test_load_history_returns_empty_list_for_unknown_conversation(
    conversation_service: ConversationService,
) -> None:
    assert conversation_service.load_history("does-not-exist") == []


def test_append_turn_then_load_history_returns_the_turn(
    conversation_service: ConversationService,
) -> None:
    turn = ConversationTurn(question="What is X?", answer="X is a widget.")

    conversation_service.append_turn("conv-1", turn)

    assert conversation_service.load_history("conv-1") == [turn]


def test_append_turn_accumulates_history_in_order(
    conversation_service: ConversationService,
) -> None:
    first = ConversationTurn(question="What is X?", answer="X is a widget.")
    second = ConversationTurn(question="What color is it?", answer="Blue.")

    conversation_service.append_turn("conv-1", first)
    conversation_service.append_turn("conv-1", second)

    assert conversation_service.load_history("conv-1") == [first, second]


def test_conversations_are_isolated_by_id(
    conversation_service: ConversationService,
) -> None:
    conversation_service.append_turn(
        "conv-1", ConversationTurn(question="Q1", answer="A1")
    )
    conversation_service.append_turn(
        "conv-2", ConversationTurn(question="Q2", answer="A2")
    )

    assert len(conversation_service.load_history("conv-1")) == 1
    assert len(conversation_service.load_history("conv-2")) == 1
    assert conversation_service.load_history("conv-1")[0].question == "Q1"


def test_load_history_returns_empty_list_for_corrupted_file(
    conversation_service: ConversationService, tmp_path: Path
) -> None:
    corrupted = tmp_path / "conversations" / "conv-1.json"
    corrupted.parent.mkdir(parents=True, exist_ok=True)
    corrupted.write_text("not valid json")

    assert conversation_service.load_history("conv-1") == []
