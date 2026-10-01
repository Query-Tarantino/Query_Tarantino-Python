from __future__ import annotations

from abc import ABC, abstractmethod


class BookDownloader(ABC):
    @abstractmethod
    def raw_text(self, book_id: int) -> str:
        pass
