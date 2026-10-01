from __future__ import annotations

import requests

from ..model import DownloadException, FailureReason
from ..ports import BookDownloader


class GutenbergHttpDownloader(BookDownloader):
    _URL_TEMPLATE = "https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    _USER_AGENT = "query-tarantino/1.0 (ULPGC Big Data course project)"
    _TIMEOUT = 30

    def raw_text(self, book_id: int) -> str:
        url = self._URL_TEMPLATE.format(book_id=book_id)
        headers = {"User-Agent": self._USER_AGENT}
        try:
            response = requests.get(url, headers=headers, timeout=self._TIMEOUT)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                raise DownloadException(
                    FailureReason.NOT_FOUND, f"Book {book_id} not found"
                )
            else:
                raise DownloadException(
                    FailureReason.NETWORK_ERROR, f"HTTP error {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            raise DownloadException(FailureReason.NETWORK_ERROR, f"Network error: {e}")
