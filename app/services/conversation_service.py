import logging
from pathlib import Path

from app.schemas.document import ConversationRecord, ConversationTurn

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, storage_directory: Path) -> None:
        self._storage_directory = storage_directory
        self._storage_directory.mkdir(parents=True, exist_ok=True)

    def _path_for(self, conversation_id: str) -> Path:
        return self._storage_directory / f"{conversation_id}.json"

    def load_history(self, conversation_id: str) -> list[ConversationTurn]:
        """
        Return the prior turns for a conversation, oldest first. A missing
        file just means this is a new conversation - not an error. A file
        that exists but fails to parse is logged and treated as empty
        rather than failing the whole request: losing memory of earlier
        turns degrades a conversation to a fresh one, it doesn't break it.
        """
        path = self._path_for(conversation_id)

        if not path.exists():
            return []

        try:
            record = ConversationRecord.model_validate_json(path.read_text())
            return record.turns
        except Exception:
            logger.exception(
                "Failed to load conversation history | conversation_id=%s",
                conversation_id,
            )
            return []

    def append_turn(self, conversation_id: str, turn: ConversationTurn) -> None:
        """Persist a new turn on top of whatever history already exists."""
        turns = self.load_history(conversation_id)
        turns.append(turn)

        record = ConversationRecord(conversation_id=conversation_id, turns=turns)
        self._path_for(conversation_id).write_text(record.model_dump_json(indent=2))

        logger.info(
            "Conversation turn persisted | conversation_id=%s | turn_count=%s",
            conversation_id,
            len(turns),
        )
