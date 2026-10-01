"""Inverted index benchmark — measures build time, RAM, and disk usage."""
import json
import os
import tracemalloc

import mongomock
import services.indexer.adapters.mongodb_index_adapter

services.indexer.adapters.mongodb_index_adapter.MongoClient = mongomock.MongoClient

import pytest

from services.indexer.adapters.folder_per_term_index_adapter import (
    FolderPerTermIndexAdapter,
)
from services.indexer.adapters.mongodb_index_adapter import MongodbIndexAdapter
from services.indexer.adapters.monolithic_json_index_adapter import (
    MonolithicJsonIndexAdapter,
)
from services.indexer.model.term_occurrences import TermOccurrences

# Simulate a realistic vocabulary: 200 unique terms across 20 books
TERMS = [f"word_{i}" for i in range(200)]
NUM_BOOKS = 20


def _build_index(adapter):
    for book_id in range(1, NUM_BOOKS + 1):
        freqs = {TERMS[i]: (book_id + i) % 10 + 1 for i in range(0, 200, 10)}
        occ = TermOccurrences(book_id=book_id, frequencies=freqs)
        adapter.add(occ)
    adapter.flush()


def _dir_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def _make_adapter(adapter_class, tmp_path):
    if adapter_class == MongodbIndexAdapter:
        return adapter_class("mongodb://localhost:27017")
    elif adapter_class == MonolithicJsonIndexAdapter:
        return adapter_class(tmp_path / "inverted_index.json")
    else:
        return adapter_class(tmp_path / "inverted_index")


ADAPTERS = [FolderPerTermIndexAdapter, MonolithicJsonIndexAdapter, MongodbIndexAdapter]


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_benchmark_indexing(benchmark, tmp_path, adapter_class):
    """Measures indexing build time for each inverted index strategy."""
    adapter = _make_adapter(adapter_class, tmp_path)

    def action():
        _build_index(adapter)

    benchmark.pedantic(action, iterations=1, rounds=5)


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_indexing_ram_usage(tmp_path, adapter_class):
    """Measures peak RAM consumed while building the inverted index."""
    adapter = _make_adapter(adapter_class, tmp_path)

    tracemalloc.start()
    _build_index(adapter)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"\n[RAM] {adapter_class.__name__}: {peak_mb:.4f} MB peak")


@pytest.mark.parametrize(
    "adapter_class",
    [FolderPerTermIndexAdapter, MonolithicJsonIndexAdapter],
)
def test_indexing_disk_usage(tmp_path, adapter_class):
    """Measures disk space used by the inverted index (file-based only)."""
    data_dir = tmp_path / "index_data"
    data_dir.mkdir()
    if adapter_class == MonolithicJsonIndexAdapter:
        adapter = adapter_class(data_dir / "inverted_index.json")
    else:
        adapter = adapter_class(data_dir)

    _build_index(adapter)
    disk_kb = _dir_size(data_dir) / 1024

    print(f"\n[DISK] {adapter_class.__name__}: {disk_kb:.2f} KB")
