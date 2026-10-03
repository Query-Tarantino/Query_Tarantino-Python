from dataclasses import dataclass
from typing import List

from .book_metadata import BookMetadata


@dataclass(frozen=True)
class SearchResult:
    query: str
    books: List[BookMetadata]
