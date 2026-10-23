"""Application-owned logging configuration."""

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
