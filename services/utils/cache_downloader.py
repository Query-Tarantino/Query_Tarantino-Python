import os
import urllib.request
from pathlib import Path

def ensure_cache(workload_path: Path, cache_path: Path, needed_books: int = 10000):
    cache_path.mkdir(parents=True, exist_ok=True)
    book_ids_file = workload_path / "book_ids.txt"
    if not book_ids_file.exists():
        return []

    with open(book_ids_file, "r") as f:
        book_ids = [line.strip() for line in f if line.strip().isdigit()]

    available_ids = []
    
    for book_id in book_ids:
        if len(available_ids) >= needed_books:
            break
            
        file_path = cache_path / f"{book_id}.txt"
        if file_path.exists():
            available_ids.append(int(book_id))
            continue

        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                text = response.read().decode('utf-8')
                with open(file_path, "w", encoding="utf-8") as out:
                    out.write(text)
            available_ids.append(int(book_id))
        except Exception as e:
            print(f"Skipping {book_id} download failed: {e}")

    return available_ids

def load_cached_book(cache_path: Path, book_id: int) -> str:
    with open(cache_path / f"{book_id}.txt", "r", encoding="utf-8") as f:
        return f.read()
