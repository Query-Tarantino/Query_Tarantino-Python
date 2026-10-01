from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..model import BookText, StoredPaths


class DatalakeStorage(ABC):
    @abstractmethod
    def save(self, book: BookText) -> StoredPaths:
        pass

    @abstractmethod
    def paths_of(self, book_id: int) -> Optional[StoredPaths]:
        pass
