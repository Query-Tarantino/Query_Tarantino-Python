from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from .adapters import (BatchBasedDatalakeAdapter, BookBasedDatalakeAdapter,
                       GutenbergHttpDownloader, TimeBasedDatalakeAdapter)
from .commands import IngestBookCommand
from .crawler_config import CrawlerConfig
from .ports import DatalakeStorage


class CrawlerFactory:
    _DATALAKE_LAYOUTS: Dict[str, Callable[[Path], DatalakeStorage]] = {
        "time": lambda path: TimeBasedDatalakeAdapter(path),
        "book": lambda path: BookBasedDatalakeAdapter(path),
        "batch": lambda path: BatchBasedDatalakeAdapter(path),
    }

    @staticmethod
    def ingest_command(config: CrawlerConfig) -> IngestBookCommand:
        return IngestBookCommand(
            downloader=GutenbergHttpDownloader(),
            datalake=CrawlerFactory.datalake(config),
        )

    @staticmethod
    def datalake(config: CrawlerConfig) -> DatalakeStorage:
        layout_func = CrawlerFactory._DATALAKE_LAYOUTS.get(config.datalake_layout)
        if layout_func is None:
            raise ValueError(f"Unknown datalake layout: {config.datalake_layout}")
        return layout_func(config.datalake)
