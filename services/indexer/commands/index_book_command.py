from __future__ import annotations

from ..model.book_text import BookText
from ..model.header_parser import HeaderParser
from ..model.term_occurrences import TermOccurrences
from ..model.tokenizer import Tokenizer
from ..ports.datalake_reader import DatalakeReader
from ..ports.inverted_index_storage import InvertedIndexStorage
from ..ports.metadata_storage import MetadataStorage
from .index_result import IndexResult


class IndexBookCommand:
    def __init__(
        self,
        datalake: DatalakeReader,
        header_parser: HeaderParser,
        tokenizer: Tokenizer,
        inverted_index: InvertedIndexStorage,
        metadata: MetadataStorage,
    ):
        self.datalake = datalake
        self.header_parser = header_parser
        self.tokenizer = tokenizer
        self.inverted_index = inverted_index
        self.metadata = metadata

    def execute(self, book_id: int) -> IndexResult:
        text = self.datalake.book_text(book_id)
        if text:
            return self._index(text)
        return IndexResult.not_found(book_id)

    def _index(self, text: BookText) -> IndexResult:
        self.metadata.save(self.header_parser.book(text))
        occurrences = self.tokenizer.occurrences(text.book_id, text.body)
        self._store(occurrences)
        return IndexResult.success(text.book_id, len(occurrences.frequencies))

    def _store(self, occurrences: TermOccurrences) -> None:
        self.inverted_index.add(occurrences)
        self.inverted_index.flush()
