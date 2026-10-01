import sys

from .indexer_config import IndexerConfig
from .indexer_factory import IndexerFactory


def main():
    config = IndexerConfig.from_environment()
    index = IndexerFactory.index_command(config)
    for arg in sys.argv[1:]:
        book_id = int(arg)
        result = index.execute(book_id)
        print(result)


if __name__ == "__main__":
    main()
