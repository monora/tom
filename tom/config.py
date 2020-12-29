import logging
import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEBUG = True if os.getenv('TOM_DEBUG', False) in ['1', 'true'] else False

TOM_OUTPUT_DIR: Optional[str] = os.getenv('TOM_OUTPUT_DIR')

log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=log_level)


def output_dir() -> Path:
    if TOM_OUTPUT_DIR:
        return Path(TOM_OUTPUT_DIR)
    else:
        return Path(PROJECT_ROOT) / '../build'


def output_file(filename: str, subdir: str = '.', suffix: str = '') -> Path:
    if len(suffix) > 0:
        filename = filename + '.' + suffix
    p = output_dir() / str(subdir)
    # Ensure subdir exists
    p.mkdir(parents=True, exist_ok=True)
    return p / filename
