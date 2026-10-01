from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..model.book_text import BookText


class DatalakeReader(ABC):
    @abstractmethod
    def book_text(self, book_id: int) -> Optional[BookText]:
        pass
