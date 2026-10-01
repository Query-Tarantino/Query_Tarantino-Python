"""Datalake write throughput benchmark — measures time, RAM, and disk usage."""
import json
import os
import tracemalloc

import pytest

from services.crawler.adapters.batch_based_datalake_adapter import (
    BatchBasedDatalakeAdapter,
)
from services.crawler.adapters.book_based_datalake_adapter import (
    BookBasedDatalakeAdapter,
)
from services.crawler.adapters.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from services.crawler.model.book_text import BookText

ADAPTERS = [TimeBasedDatalakeAdapter, BookBasedDatalakeAdapter, BatchBasedDatalakeAdapter]
NUM_BOOKS = 50

DUMMY_HEADER = "Title: Benchmark Book\nAuthor: Test Author\nLanguage: English"
DUMMY_BODY = "It was a dark and stormy night. " * 200  # ~6 KB per book


def _dir_size(path):
    """Return total bytes consumed by all files under *path*."""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def _write_books(adapter, n):
    for i in range(1, n + 1):
        book = BookText(book_id=i, header=DUMMY_HEADER, body=DUMMY_BODY)
        adapter.save(book)


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_benchmark_datalake_write(benchmark, tmp_path, adapter_class):
    """Measures write throughput (time) for each datalake layout."""
    adapter = adapter_class(tmp_path)

    def action():
        _write_books(adapter, NUM_BOOKS)

    benchmark.pedantic(action, iterations=1, rounds=5)


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_datalake_ram_usage(tmp_path, adapter_class):
    """Measures peak RAM consumed while writing books."""
    adapter = adapter_class(tmp_path)

    tracemalloc.start()
    _write_books(adapter, NUM_BOOKS)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    result = {
        "adapter": adapter_class.__name__,
        "metric": "peak_ram_mb",
        "value": round(peak_mb, 4),
    }
    with open(results_dir / f"ram_{adapter_class.__name__}.json", "w") as f:
        json.dump(result, f)

    print(f"\n[RAM] {adapter_class.__name__}: {peak_mb:.4f} MB peak")


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_datalake_disk_usage(tmp_path, adapter_class):
    """Measures total disk space consumed after writing books."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    adapter = adapter_class(data_dir)

    _write_books(adapter, NUM_BOOKS)
    disk_bytes = _dir_size(data_dir)
    disk_kb = disk_bytes / 1024

    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    result = {
        "adapter": adapter_class.__name__,
        "metric": "disk_usage_kb",
        "value": round(disk_kb, 2),
    }
    with open(results_dir / f"disk_{adapter_class.__name__}.json", "w") as f:
        json.dump(result, f)

    print(f"\n[DISK] {adapter_class.__name__}: {disk_kb:.2f} KB")
