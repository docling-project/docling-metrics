import logging
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel

_log = logging.getLogger(__name__)


class FileEntry(BaseModel):
    filename: Path
    content: str


class TextFileLoader:
    def __init__(self, input_dir: Path, file_pattern: str = "*.md"):
        r""" """
        self._file_pattern = file_pattern
        self._input_dir = input_dir

    def load(self) -> Iterator[FileEntry]:
        r"""Yield FileEntry"""

        files = sorted(self._input_dir.glob(self._file_pattern))
        _log.info(f"Found {len(files)} files in: %s", str(self._input_dir))

        for md_file in files:
            content = md_file.read_text(encoding="utf-8")
            file_entry = FileEntry(filename=md_file, content=content)
            yield file_entry
