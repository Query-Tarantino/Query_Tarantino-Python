from __future__ import annotations

import sys
from itertools import takewhile
from pathlib import Path
from typing import List

from services.control.adapters.file_control_state_store import \
    FileControlStateStore
from services.control.adapters.local_crawler import LocalCrawler
from services.control.adapters.local_indexer import LocalIndexer
from services.control.commands.control_pipeline import ControlPipeline
from services.control.control_config import ControlConfig
from services.control.model.step_report import StepReport
from services.crawler.crawler_config import CrawlerConfig
from services.crawler.crawler_factory import CrawlerFactory
from services.indexer.indexer_config import IndexerConfig
from services.indexer.indexer_factory import IndexerFactory

DEFAULT_CANDIDATES = "sample_ids.txt"


def main(args: List[str]) -> None:
    config = ControlConfig.from_environment()
    pipe = pipeline(config, candidates_file(config, args))

    def step_generator():
        while True:
            yield pipe.run_step()

    for report in takewhile(lambda r: not r.idle(), step_generator()):
        print_report(report)

    print("[CONTROL] Nothing left to do")


def pipeline(config: ControlConfig, candidates_file_path: Path) -> ControlPipeline:
    return ControlPipeline(
        FileControlStateStore(config.control),
        LocalCrawler(CrawlerFactory.ingest_command(CrawlerConfig.from_environment())),
        LocalIndexer(IndexerFactory.index_command(IndexerConfig.from_environment())),
        candidates(candidates_file_path),
    )


def candidates_file(config: ControlConfig, args: List[str]) -> Path:
    filename = args[0] if len(args) > 0 else DEFAULT_CANDIDATES
    return config.workload / filename


def candidates(file_path: Path) -> List[int]:
    return [int(line.strip()) for line in lines(file_path) if line.strip()]


def lines(file_path: Path) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def print_report(report: StepReport) -> None:
    print(f"[CONTROL] {report.description()}")


if __name__ == "__main__":
    main(sys.argv[1:])
