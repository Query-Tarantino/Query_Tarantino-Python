"""Metadata storage benchmark — measures insertion time, RAM, and disk usage."""
import json
import os
import tracemalloc
from pathlib import Path

import mongomock
import services.indexer.adapters.mongodb_metadata_adapter

services.indexer.adapters.mongodb_metadata_adapter.MongoClient = mongomock.MongoClient

import pytest

from services.indexer.adapters.mongodb_metadata_adapter import MongodbMetadataAdapter
from services.indexer.adapters.sqlite_metadata_adapter import SqliteMetadataAdapter
from services.indexer.model.book import Book

ADAPTERS = [SqliteMetadataAdapter, MongodbMetadataAdapter]
NUM_BOOKS = 50


def _make_books(n):
    return [
        Book(
            book_id=i,
            title=f"Book Title {i}",
            author=f"Author {i}",
            language="English",
            path=Path(f"/datalake/{i}.body.txt"),
        )
        for i in range(1, n + 1)
    ]


def _dir_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def _make_adapter(adapter_class, tmp_path):
    if adapter_class == MongodbMetadataAdapter:
        return adapter_class("mongodb://localhost:27017")
    else:
        return adapter_class(tmp_path / "metadata.db")


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_benchmark_metadata(benchmark, tmp_path, adapter_class):
    """Measures insertion speed for metadata storage."""
    adapter = _make_adapter(adapter_class, tmp_path)
    books = _make_books(NUM_BOOKS)

    def action():
        for book in books:
            adapter.save(book)

    benchmark.pedantic(action, iterations=1, rounds=5)


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_metadata_ram_usage(tmp_path, adapter_class):
    """Measures peak RAM consumed while inserting metadata."""
    adapter = _make_adapter(adapter_class, tmp_path)
    books = _make_books(NUM_BOOKS)

    tracemalloc.start()
    for book in books:
        adapter.save(book)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"\n[RAM] {adapter_class.__name__}: {peak_mb:.4f} MB peak")


@pytest.mark.parametrize(
    "adapter_class", [SqliteMetadataAdapter]
)
def test_metadata_disk_usage(tmp_path, adapter_class):
    """Measures disk usage of the metadata database (file-based only)."""
    data_dir = tmp_path / "meta_data"
    data_dir.mkdir()
    adapter = adapter_class(data_dir / "metadata.db")
    books = _make_books(NUM_BOOKS)

    for book in books:
        adapter.save(book)

    disk_kb = _dir_size(data_dir) / 1024
    print(f"\n[DISK] {adapter_class.__name__}: {disk_kb:.2f} KB")
