from __future__ import annotations

from services.control.model.outcome import Outcome
from services.control.ports.indexer import Indexer
from services.indexer.commands.index_book_command import IndexBookCommand
from services.indexer.commands.index_result import IndexResult


class LocalIndexer(Indexer):
    def __init__(self, index_command: IndexBookCommand):
        self.index_command = index_command

    def index(self, book_id: int) -> Outcome:
        return self._outcome(self.index_command.execute(book_id))

    @staticmethod
    def _outcome(result: IndexResult) -> Outcome:
        if result.indexed:
            return Outcome.success(f"{result.unique_terms} unique terms indexed")
        else:
            return Outcome.failure("skipped, not found in the datalake")
