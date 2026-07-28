from app.schemas.document import ConversationTurn, SearchResult
from app.services.answer_service import AnswerService
from tests.fakes import FakeGroqClient


def _make_result(text: str, citation: str) -> SearchResult:
    return SearchResult(
        document_id="doc-1",
        filename="notes.txt",
        chunk_index=0,
        text=text,
        start_offset=0,
        end_offset=len(text),
        distance=0.1,
        citation=citation,
    )


def test_generate_answer_returns_fallback_message_for_no_chunks() -> None:
    service = AnswerService(client=FakeGroqClient())

    answer = service.generate_answer("What is X?", [])

    assert "don't have any relevant documents" in answer.lower()


def test_generate_answer_returns_model_response_text() -> None:
    fake_client = FakeGroqClient(response_text="X is a widget. [1]")
    service = AnswerService(client=fake_client)
    chunk = _make_result("X is a widget.", "notes.txt (chunk 0, characters 0-14)")

    answer = service.generate_answer("What is X?", [chunk])

    assert answer == "X is a widget. [1]"


def test_generate_answer_includes_context_and_question_in_prompt() -> None:
    fake_client = FakeGroqClient()
    service = AnswerService(client=fake_client)
    chunk = _make_result("X is a widget.", "notes.txt (chunk 0, characters 0-14)")

    service.generate_answer("What is X?", [chunk])

    prompt = fake_client.last_call["messages"][-1]["content"]
    assert "X is a widget." in prompt
    assert "notes.txt (chunk 0, characters 0-14)" in prompt
    assert "What is X?" in prompt


def test_generate_answer_with_no_history_sends_system_and_question_only() -> None:
    fake_client = FakeGroqClient()
    service = AnswerService(client=fake_client)
    chunk = _make_result("X is a widget.", "notes.txt (chunk 0, characters 0-14)")

    service.generate_answer("What is X?", [chunk])

    messages = fake_client.last_call["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_generate_answer_replays_history_before_the_current_question() -> None:
    fake_client = FakeGroqClient()
    service = AnswerService(client=fake_client)
    chunk = _make_result("X is a widget.", "notes.txt (chunk 0, characters 0-14)")
    history = [ConversationTurn(question="What is X?", answer="X is a widget. [1]")]

    service.generate_answer("What color is it?", [chunk], history=history)

    messages = fake_client.last_call["messages"]
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "What is X?"}
    assert messages[2] == {"role": "assistant", "content": "X is a widget. [1]"}
    assert "What color is it?" in messages[3]["content"]


def test_empty_string_api_key_is_treated_as_unset() -> None:
    # An empty string ("" from an unfilled .env placeholder) must not be
    # passed through as-is: groq.Groq(api_key="") skips the SDK's normal
    # "key not set" check and fails confusingly later, at request time.
    service = AnswerService(api_key="")

    assert service._api_key is None


def test_generate_answer_constructs_client_lazily() -> None:
    calls = []

    class CountingService(AnswerService):
        def _get_client(self):
            calls.append(1)
            return super()._get_client()

    service = CountingService(client=FakeGroqClient())
    chunk = _make_result("X is a widget.", "notes.txt (chunk 0, characters 0-14)")
    service.generate_answer("What is X?", [chunk])

    assert len(calls) == 1
    assert service._client is not None
