from __future__ import annotations

from typing import Callable, Dict

from .adapters.batch_based_datalake_reader import BatchBasedDatalakeReader
from .adapters.book_based_datalake_reader import BookBasedDatalakeReader
from .adapters.file_stopwords_loader import FileStopwordsLoader
from .adapters.folder_per_term_index_adapter import FolderPerTermIndexAdapter
from .adapters.mongodb_index_adapter import MongodbIndexAdapter
from .adapters.mongodb_metadata_adapter import MongodbMetadataAdapter
from .adapters.monolithic_json_index_adapter import MonolithicJsonIndexAdapter
from .adapters.sqlite_metadata_adapter import SqliteMetadataAdapter
from .adapters.time_based_datalake_reader import TimeBasedDatalakeReader
from .commands.index_book_command import IndexBookCommand
from .indexer_config import IndexerConfig
from .model.header_parser import HeaderParser
from .model.tokenizer import Tokenizer
from .ports.datalake_reader import DatalakeReader
from .ports.inverted_index_storage import InvertedIndexStorage
from .ports.metadata_storage import MetadataStorage


class IndexerFactory:
    DATALAKE_LAYOUTS: Dict[str, Callable[[IndexerConfig], DatalakeReader]] = {
        "time": lambda config: TimeBasedDatalakeReader(config.datalake),
        "book": lambda config: BookBasedDatalakeReader(config.datalake),
        "batch": lambda config: BatchBasedDatalakeReader(config.datalake),
    }

    INDEX_STRUCTURES: Dict[str, Callable[[IndexerConfig], InvertedIndexStorage]] = {
        "json": lambda config: MonolithicJsonIndexAdapter(
            config.datamarts / "inverted_index.json"
        ),
        "folders": lambda config: FolderPerTermIndexAdapter(
            config.datamarts / "inverted_index"
        ),
        "mongo": lambda config: MongodbIndexAdapter(config.mongo_uri),
    }

    METADATA_BACKENDS: Dict[str, Callable[[IndexerConfig], MetadataStorage]] = {
        "sqlite": lambda config: SqliteMetadataAdapter(
            config.datamarts / "metadata.db"
        ),
        "mongo": lambda config: MongodbMetadataAdapter(config.mongo_uri),
    }

    @staticmethod
    def index_command(config: IndexerConfig) -> IndexBookCommand:
        return IndexBookCommand(
            IndexerFactory.datalake_reader(config),
            HeaderParser(),
            IndexerFactory.tokenizer(config),
            IndexerFactory.inverted_index(config),
            IndexerFactory.metadata(config),
        )

    @staticmethod
    def datalake_reader(config: IndexerConfig) -> DatalakeReader:
        return IndexerFactory._option(
            IndexerFactory.DATALAKE_LAYOUTS, config.datalake_layout, "Datalake Layout"
        )(config)

    @staticmethod
    def inverted_index(config: IndexerConfig) -> InvertedIndexStorage:
        return IndexerFactory._option(
            IndexerFactory.INDEX_STRUCTURES, config.index, "Index Structure"
        )(config)

    @staticmethod
    def metadata(config: IndexerConfig) -> MetadataStorage:
        return IndexerFactory._option(
            IndexerFactory.METADATA_BACKENDS, config.metadata, "Metadata Backend"
        )(config)

    @staticmethod
    def tokenizer(config: IndexerConfig) -> Tokenizer:
        return Tokenizer(
            FileStopwordsLoader(config.workload / "stopwords.txt").stopwords()
        )

    @staticmethod
    def _option(options: dict, name: str, kind: str):
        if name not in options:
            raise ValueError(f"Unknown {kind}: {name}")
        return options[name]
