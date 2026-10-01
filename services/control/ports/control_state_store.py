from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Set


class ControlStateStore(ABC):
    @abstractmethod
    def downloaded(self) -> Set[int]:
        pass

    @abstractmethod
    def indexed(self) -> Set[int]:
        pass

    @abstractmethod
    def mark_downloaded(self, book_id: int) -> None:
        pass

    @abstractmethod
    def mark_indexed(self, book_id: int) -> None:
        pass
