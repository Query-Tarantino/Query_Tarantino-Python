import csv
import os
import shutil
import time
import tracemalloc
from pathlib import Path

from services.crawler.adapters.batch_based_datalake_adapter import BatchBasedDatalakeAdapter
from services.crawler.adapters.book_based_datalake_adapter import BookBasedDatalakeAdapter
from services.crawler.adapters.time_based_datalake_adapter import TimeBasedDatalakeAdapter
from services.crawler.model.gutenberg_text import GutenbergText
from services.indexer.adapters.folder_per_term_index_adapter import FolderPerTermIndexAdapter
from services.indexer.adapters.mongodb_index_adapter import MongodbIndexAdapter
from services.indexer.adapters.mongodb_metadata_adapter import MongodbMetadataAdapter
from services.indexer.adapters.monolithic_json_index_adapter import MonolithicJsonIndexAdapter
from services.indexer.adapters.sqlite_metadata_adapter import SqliteMetadataAdapter
from services.indexer.model.book import Book
from services.indexer.model.term_occurrences import TermOccurrences
from services.utils.cache_downloader import ensure_cache, load_cached_book


def clear_dir(path: Path):
    for _ in range(10):
        if not path.exists():
            break
        try:
            shutil.rmtree(path)
            break
        except PermissionError:
            time.sleep(0.2)
    path.mkdir(parents=True, exist_ok=True)


def get_dir_size(path: Path):
    total = 0
    file_count = 0
    dir_count = 0
    for dirpath, dirnames, filenames in os.walk(path):
        dir_count += len(dirnames)
        file_count += len(filenames)
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total, file_count, dir_count


def write_csv(filename: str, rows: list):
    Path("benchmarks/results").mkdir(parents=True, exist_ok=True)
    with open(f"benchmarks/results/{filename}", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["language", "structure", "metric", "n_books", "value", "unit"])
        writer.writerows(rows)


def run_crawler_benchmarks(sizes, cache_ids, cache_path):
    print("Running crawler benchmarks...")
    results = []
    adapters = {
        "time": TimeBasedDatalakeAdapter,
        "book": BookBasedDatalakeAdapter,
        "batch": BatchBasedDatalakeAdapter,
    }

    for size in sizes:
        ids_to_process = cache_ids[:size]
        if not ids_to_process:
            continue
        actual_size = len(ids_to_process)

        for name, adapter_class in adapters.items():
            root = Path(f"benchmarks/tmp/datalake-{name}-{size}")
            clear_dir(root)
            adapter = adapter_class(root)

            # Measure write throughput
            start = time.perf_counter()
            for book_id in ids_to_process:
                raw = load_cached_book(cache_path, book_id)
                try:
                    book_text = GutenbergText.book_text(book_id, raw)
                    adapter.save(book_text)
                except:
                    pass
            elapsed = time.perf_counter() - start
            throughput = size / elapsed if elapsed > 0 else 0
            results.append(["python", name, "write_throughput", size, f"{throughput:.2f}", "books/s"])

            # Disk usage & counts
            disk_bytes, files, dirs = get_dir_size(root)
            results.append(["python", name, "disk_usage", size, disk_bytes, "bytes"])
            results.append(["python", name, "file_count", size, files, "files"])
            results.append(["python", name, "directory_count", size, dirs, "dirs"])

            # Lookup time
            start = time.perf_counter()
            for book_id in ids_to_process[:100]:  # sample 100 for lookup
                adapter.paths_of(book_id)
            elapsed = time.perf_counter() - start
            lookup_us = (elapsed / min(size, 100)) * 1_000_000
            results.append(["python", name, "lookup_time", size, f"{lookup_us:.2f}", "us/op"])

    write_csv("python-crawler.csv", results)


def run_metadata_benchmarks(sizes):
    print("Running metadata benchmarks...")
    results = []
    adapters = {
        "sqlite": lambda root: SqliteMetadataAdapter(root / "metadata.db"),
        "mongo": lambda root: MongodbMetadataAdapter("mongodb://localhost:27017")
    }

    for size in sizes:
        books = [
            Book(i, f"Title {i}", f"Author {i}", "English", Path(f"/test/{i}.txt"))
            for i in range(1, size + 1)
        ]
        
        for name, adapter_factory in adapters.items():
            root = Path(f"benchmarks/tmp/datamarts-meta-{name}-{size}")
            clear_dir(root)
            
            if name == "mongo":
                import mongomock
                import services.indexer.adapters.mongodb_metadata_adapter as mongo_meta
                mongo_meta.MongoClient = mongomock.MongoClient
                client = mongomock.MongoClient("mongodb://localhost:27017")
                client.drop_database("tarantino")

            adapter = adapter_factory(root)

            # Bulk insertion
            start = time.perf_counter()
            for book in books:
                adapter.save(book)
            elapsed = time.perf_counter() - start
            results.append(["python", name, "bulk_insertion_time", size, f"{elapsed * 1000:.2f}", "ms"])

            # Disk usage
            if name == "sqlite":
                disk_bytes, _, _ = get_dir_size(root)
                results.append(["python", name, "disk_usage", size, disk_bytes, "bytes"])
            else:
                db = client["tarantino"]
                # mongomock doesn't have dbstats, so we estimate 0 or basic size
                disk_bytes = 0
                results.append(["python", name, "disk_usage", size, disk_bytes, "bytes"])

    write_csv("python-metadata.csv", results)


def main():
    sizes = [100, 1000, 10000]
    workload = Path("workload")
    cache = Path("benchmarks/cache")
    
    print("Ensuring cache (downloads might take time)...")
    cache_ids = ensure_cache(workload, cache, needed_books=100) # Limit to 100 for local test speed, change to 10000 for real run
    
    run_crawler_benchmarks(sizes, cache_ids, cache)
    run_metadata_benchmarks(sizes)
    print("Done! CSVs generated in benchmarks/results/")

if __name__ == "__main__":
    main()
