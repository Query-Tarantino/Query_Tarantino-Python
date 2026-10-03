from __future__ import annotations

from abc import ABC, abstractmethod

from services.control.model.outcome import Outcome


class Indexer(ABC):
    @abstractmethod
    def index(self, book_id: int) -> Outcome:
        pass
