from __future__ import annotations

from ..model import DownloadException, FailureReason, GutenbergText
from ..ports import BookDownloader, DatalakeStorage
from .ingest_result import IngestResult


class IngestBookCommand:
    def __init__(self, downloader: BookDownloader, datalake: DatalakeStorage):
        self._downloader = downloader
        self._datalake = datalake

    def execute(self, book_id: int) -> IngestResult:
        paths = self._datalake.paths_of(book_id)
        if paths is not None:
            return IngestResult.success(book_id, paths)
        return self._download_and_store(book_id)

    def _download_and_store(self, book_id: int) -> IngestResult:
        try:
            raw_text = self._downloader.raw_text(book_id)
            book_text = GutenbergText.book_text(book_id, raw_text)
            paths = self._datalake.save(book_text)
            return IngestResult.success(book_id, paths)
        except DownloadException as e:
            return IngestResult.failure_result(book_id, e.reason)
        except OSError:
            return IngestResult.failure_result(book_id, FailureReason.STORAGE_ERROR)
