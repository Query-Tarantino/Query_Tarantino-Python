# Query Tarantino â€” Stage 1: Data Layer (Python)

Python implementation of the data layer of a search engine over [Project Gutenberg](https://www.gutenberg.org/) books:
a **datalake** with the raw texts, **datamarts** with metadata and an inverted index, and a minimal **control layer**
that coordinates downloading and indexing.

The behavior shared with the Java and C# implementations (split rules, datalake layouts, tokenizer,
datamart formats, control algorithm and benchmark format) is defined in [SPEC.md](SPEC.md).

## Repository structure

```
services/
  crawler/    downloads books, splits header/body and stores them in the datalake
  indexer/    reads the datalake and builds the inverted index and the metadata datamart
  query/      searches the datamarts
  control/    orchestrates crawler -> indexer and tracks progress in control files
workload/     experiment definition shared by every language implementation
  book_ids.txt     book ids used by the benchmarks (the first N are taken)
  sample_ids.txt   small sample dataset to test the pipeline quickly
  stopwords.txt    stopwords removed by the tokenizer
  queries.txt      fixed query workload for the search benchmark
```

Each service follows the same layout (Python packages):

```
services/<service>/
  model/      dataclasses and pure domain logic
  ports/      abstract base classes the service depends on
  adapters/   implementations of the ports (filesystem, HTTP, SQLite, MongoDB)
  commands/   use cases
  __main__.py, config.py, factory.py
services/<service>/tests/benchmarking/
```

The following directories are **created at runtime** in the project root and are not versioned:

| Directory     | Written by | Content                                                              |
|---------------|------------|----------------------------------------------------------------------|
| `datalake/`   | crawler    | `<id>.header.txt` / `<id>.body.txt` in the selected layout           |
| `datamarts/`  | indexer    | `inverted_index.json`, `inverted_index/`, `metadata.db`              |
| `control/`    | control    | `downloaded_books.txt`, `indexed_books.txt`                          |
| `benchmarks/` | benchmarks | `<service>/pytest-results.csv`, download cache and temporary data       |

## Requirements

- Python 3.12+
- pip
- MongoDB (only for the `mongo` index or metadata backends), e.g.
  `docker run -d -p 27017:27017 --name tarantino-mongo mongo:7`

## Configuration

Every setting has a default that works when running from the project root. Override them with environment variables:

| Variable                    | Default                     | Values                   |
|-----------------------------|-----------------------------|--------------------------|
| `TARANTINO_DATALAKE`        | `datalake`                  | path                     |
| `TARANTINO_DATAMARTS`       | `datamarts`                 | path                     |
| `TARANTINO_CONTROL`         | `control`                   | path                     |
| `TARANTINO_BENCHMARKS`      | `benchmarks`                | path                     |
| `TARANTINO_WORKLOAD`        | `workload`                  | path                     |
| `TARANTINO_DATALAKE_LAYOUT` | `time`                      | `time`, `book`, `batch`  |
| `TARANTINO_INDEX`           | `json`                      | `json`, `mongo`, `folders` |
| `TARANTINO_METADATA`        | `sqlite`                    | `sqlite`, `mongo`        |
| `TARANTINO_MONGO_URI`       | `mongodb://localhost:27017` | connection string        |

The crawler and the indexer must use the same `TARANTINO_DATALAKE_LAYOUT`; the indexer and the query service must use
the same `TARANTINO_INDEX` and `TARANTINO_METADATA`.

## Running

Always run from the project root so the runtime directories are created there.

```bash
python -m venv .venv
source .venv/Scripts/activate      # On Windows Git Bash
# .\.venv\Scripts\Activate.ps1   # On Windows PowerShell
# source .venv/bin/activate      # On Linux/Mac
python -m pip install -r requirements.txt                             # install dependencies

python -m services.control                                  # full pipeline over workload/sample_ids.txt
python -m services.control book_ids.txt

python -m services.crawler 1342 84                          # ingest specific books
python -m services.indexer 1342 84                          # index specific books
python -m services.query "adventure island"
```

## Benchmarks

The benchmark suite measures **three dimensions** for each storage strategy:

| Metric | Tool | Description |
|--------|------|-------------|
| **Time** | `pytest-benchmark` | Execution latency (ms) with statistical analysis |
| **RAM** | `tracemalloc` | Peak memory consumption (MB) |
| **Disk** | `os.walk` | Total storage footprint (KB) |

### Running benchmarks

```bash
# Run all benchmarks (time only, with statistical analysis)
pytest services/ --benchmark-only

# Save results for later comparison
pytest services/ --benchmark-only --benchmark-save=my_run

# Run all benchmarks + generate charts (time + RAM + disk)
python -m services.utils.plot_benchmarks
```

Charts are saved to `benchmarks/` (not versioned).

### What is compared

| Comparison                  | Structures                     | Metrics                                                                 | Benchmark                         |
|-----------------------------|--------------------------------|-------------------------------------------------------------------------|-----------------------------------|
| Datalake (PDF 3.1)          | `time`, `book`, `batch`        | write throughput, lookup, recovery, RAM, disk overhead                   | crawler `test_datalake_benchmark.py`, `test_datalake_recovery.py` |
| Inverted index (PDF 4.2)    | `json`, `mongo`, `folders`     | build time, query time, RAM, disk                                       | indexer `test_indexing_benchmark.py`, query `test_query_benchmark.py` |
| Metadata (PDF 4.1)          | `sqlite`, `mongo`              | insertion speed, RAM, disk                                              | indexer `test_metadata_benchmark.py` |

The rules that keep results comparable across languages (dataset, sizes, iterations, metrics and
units) are defined in [SPEC.md](SPEC.md#11-benchmarks).
