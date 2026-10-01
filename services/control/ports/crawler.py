from __future__ import annotations

from abc import ABC, abstractmethod

from services.control.model.outcome import Outcome


class Crawler(ABC):
    @abstractmethod
    def ingest(self, book_id: int) -> Outcome:
        pass
