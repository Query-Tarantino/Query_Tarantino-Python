from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterator, Set

from .term_occurrences import TermOccurrences


class Tokenizer:
    TERM = re.compile(r"[^\W\d_]+", re.UNICODE)
    MIN_TERM_LENGTH = 2

    def __init__(self, stopwords: Set[str]):
        self.stopwords = stopwords

    def occurrences(self, book_id: int, body: str) -> TermOccurrences:
        return TermOccurrences(book_id, self._frequencies(body))

    def _frequencies(self, body: str) -> Dict[str, int]:
        return dict(Counter(self._terms(body)))

    def _terms(self, body: str) -> Iterator[str]:
        for match in self.TERM.finditer(body.lower()):
            term = match.group()
            if self._is_indexable(term):
                yield term

    def _is_indexable(self, term: str) -> bool:
        return len(term) >= self.MIN_TERM_LENGTH and term not in self.stopwords
