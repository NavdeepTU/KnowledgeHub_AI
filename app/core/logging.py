import logging
import sys


def configure_logging() -> None:
    """
    Configure application-wide logging.

    Logs are written to the terminal for now.
    Later, we can send them to files or monitoring tools such as CloudWatch.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
