from services.utils.spec_benchmarks import run_crawler_benchmarks
from services.utils.cache_downloader import ensure_cache
from pathlib import Path
import sys

def main():
    sizes = [100, 1000, 10000]
    workload = Path("workload")
    cache = Path("benchmarks/cache")
    print("Ensuring cache (downloads might take time)...")
    cache_ids = ensure_cache(workload, cache, needed_books=100)
    run_crawler_benchmarks(sizes, cache_ids, cache)

if __name__ == "__main__":
    main()
