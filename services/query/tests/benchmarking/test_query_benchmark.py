"""Query search benchmark — measures query time and RAM for each index reader."""
import json
import tracemalloc

import mongomock
import services.query.adapters.mongodb_index_reader

services.query.adapters.mongodb_index_reader.MongoClient = mongomock.MongoClient

import pytest

from services.indexer.adapters.folder_per_term_index_adapter import (
    FolderPerTermIndexAdapter,
)
from services.indexer.adapters.monolithic_json_index_adapter import (
    MonolithicJsonIndexAdapter,
)
from services.indexer.model.term_occurrences import TermOccurrences
from services.query.adapters.folder_per_term_index_reader import (
    FolderPerTermIndexReader,
)
from services.query.adapters.mongodb_index_reader import MongodbIndexReader
from services.query.adapters.monolithic_json_index_reader import (
    MonolithicJsonIndexReader,
)

# Pre-populate index data so queries have something to find
TERMS = ["adventure", "island", "whale", "treasure", "ocean"]
QUERY_TERMS = ["adventure", "island"]


def _populate_json(path):
    """Write a small inverted index JSON file for benchmarking."""
    index = {}
    for term in TERMS:
        index[term] = list(range(1, 51))  # 50 books per term
    with open(path, "w") as f:
        json.dump(index, f)


def _populate_folders(root):
    """Write a folder-per-term index for benchmarking."""
    adapter = FolderPerTermIndexAdapter(root)
    for book_id in range(1, 51):
        freqs = {t: book_id for t in TERMS}
        adapter.add(TermOccurrences(book_id=book_id, frequencies=freqs))
    adapter.flush()


def _populate_mongo():
    """Populate the mongomock instance with index data."""
    import services.indexer.adapters.mongodb_index_adapter as mod
    mod.MongoClient = mongomock.MongoClient
    from services.indexer.adapters.mongodb_index_adapter import MongodbIndexAdapter
    adapter = MongodbIndexAdapter("mongodb://localhost:27017")
    for book_id in range(1, 51):
        freqs = {t: book_id for t in TERMS}
        adapter.add(TermOccurrences(book_id=book_id, frequencies=freqs))
    adapter.flush()
    return adapter


def _make_reader(reader_class, tmp_path):
    if reader_class == MongodbIndexReader:
        _populate_mongo()
        return reader_class("mongodb://localhost:27017")
    elif reader_class == MonolithicJsonIndexReader:
        json_path = tmp_path / "inverted_index.json"
        _populate_json(json_path)
        return reader_class(json_path)
    else:
        folder_path = tmp_path / "inverted_index"
        _populate_folders(folder_path)
        return reader_class(folder_path)


READERS = [FolderPerTermIndexReader, MonolithicJsonIndexReader, MongodbIndexReader]


@pytest.mark.parametrize("reader_class", READERS)
def test_benchmark_query(benchmark, tmp_path, reader_class):
    """Measures query response time for each index reader."""
    reader = _make_reader(reader_class, tmp_path)

    def action():
        result = None
        for term in QUERY_TERMS:
            postings = reader.postings(term)
            if result is None:
                result = postings
            else:
                result = result & postings
        return result

    benchmark.pedantic(action, iterations=10, rounds=5)


@pytest.mark.parametrize("reader_class", READERS)
def test_query_ram_usage(tmp_path, reader_class):
    """Measures peak RAM consumed during query execution."""
    reader = _make_reader(reader_class, tmp_path)

    tracemalloc.start()
    for _ in range(100):
        result = None
        for term in QUERY_TERMS:
            postings = reader.postings(term)
            if result is None:
                result = postings
            else:
                result = result & postings
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"\n[RAM] {reader_class.__name__}: {peak_mb:.4f} MB peak")
