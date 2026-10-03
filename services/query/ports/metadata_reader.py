from abc import ABC, abstractmethod
from typing import List, Optional

from ..model.book_metadata import BookMetadata


class MetadataReader(ABC):
    @abstractmethod
    def book(self, book_id: int) -> Optional[BookMetadata]:
        pass

    @abstractmethod
    def books_by(self, author: str) -> List[BookMetadata]:
        pass
