import re
from typing import Set


class QueryTerms:
    _TERM = re.compile(r"[^\W\d_]+")
    _MIN_TERM_LENGTH = 2

    @staticmethod
    def of(query: str, stopwords: Set[str]) -> Set[str]:
        terms = (match.group(0) for match in QueryTerms._TERM.finditer(query.lower()))
        filtered_terms = (
            term for term in terms if QueryTerms._is_searchable(term, stopwords)
        )
        return set(dict.fromkeys(filtered_terms))  # ordered deduplication

    @staticmethod
    def _is_searchable(term: str, stopwords: Set[str]) -> bool:
        return len(term) >= QueryTerms._MIN_TERM_LENGTH and term not in stopwords
