from __future__ import annotations

from abc import ABC, abstractmethod

from ..model.term_occurrences import TermOccurrences


class InvertedIndexStorage(ABC):
    @abstractmethod
    def add(self, occurrences: TermOccurrences) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass
