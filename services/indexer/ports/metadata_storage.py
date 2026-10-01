from __future__ import annotations

from abc import ABC, abstractmethod

from ..model.book import Book


class MetadataStorage(ABC):
    @abstractmethod
    def save(self, book: Book) -> None:
        pass
