from abc import ABC, abstractmethod
from typing import Set


class StopwordsLoader(ABC):
    @abstractmethod
    def stopwords(self) -> Set[str]:
        pass
