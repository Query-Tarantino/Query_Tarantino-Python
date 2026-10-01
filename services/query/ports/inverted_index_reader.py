from abc import ABC, abstractmethod
from typing import Set


class InvertedIndexReader(ABC):
    @abstractmethod
    def postings(self, term: str) -> Set[int]:
        pass
