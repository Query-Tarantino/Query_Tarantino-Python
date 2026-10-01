"""Datalake recovery (lookup) benchmark — measures time to locate existing books."""
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


@pytest.mark.parametrize("adapter_class", ADAPTERS)
def test_benchmark_datalake_recovery(benchmark, tmp_path, adapter_class):
    """Measures lookup cost: time needed to find an existing book's paths."""
    adapter = adapter_class(tmp_path)
    # Pre-populate 20 books so there's data to look up
    for i in range(1, 21):
        book = BookText(book_id=i, header="header", body="body")
        adapter.save(book)

    def action():
        for i in range(1, 21):
            adapter.paths_of(i)

    benchmark.pedantic(action, iterations=5, rounds=5)
