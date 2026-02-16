import logging
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel

_log = logging.getLogger(__name__)


class FileEntryInfo(BaseModel):
    id: str
    pivot_filename: Path
    target_filename: Path | None = None


class FileEntry(FileEntryInfo):
    pivot_content: str
    target_content: str | None = None


class TextFileLoader:
    def __init__(
        self,
        input_dir: Path,
        pivot_file_pattern: str = "GT_*.md",
        target_file_pattern: str = "pred_*.md",
        raise_on_missing: bool = False,
    ):
        r"""
        Initialize TextFileLoader for loading matched file pairs.

        Args:
            input_dir: Directory containing the files
            pivot_file_pattern: Pattern for pivot files (e.g., "GT_*.md")
            target_file_pattern: Pattern for target files (e.g., "pred_*.md")
            raise_on_missing: If True, raise FileNotFoundError when target file is missing
        """
        self._input_dir = input_dir
        self._pivot_file_pattern = pivot_file_pattern
        self._target_file_pattern = target_file_pattern
        self._raise_on_missing = raise_on_missing

    def load(self) -> Iterator[FileEntry]:
        r"""
        Yield FileEntry instances containing matched pivot and target file pairs.
        """
        # Find and load matched file pairs
        matches = self._find_matches(
            data_root=self._input_dir,
            pivot_file_pattern=self._pivot_file_pattern,
            target_file_pattern=self._target_file_pattern,
            raise_on_missing=self._raise_on_missing,
        )

        # Loop over matched file pairs and create FileEntry instances
        for entry_info in matches:
            pivot_content = entry_info.pivot_filename.read_text(encoding="utf-8")
            target_content = (
                entry_info.target_filename.read_text(encoding="utf-8")
                if entry_info.target_filename
                else None
            )

            file_entry = FileEntry(
                id=entry_info.id,
                pivot_filename=entry_info.pivot_filename,
                pivot_content=pivot_content,
                target_filename=entry_info.target_filename,
                target_content=target_content,
            )
            yield file_entry

    def _find_matches(
        self,
        data_root: Path,
        pivot_file_pattern: str,
        target_file_pattern: str,
        raise_on_missing: bool,
    ) -> list[FileEntryInfo]:
        """
        Match files based on patterns with wildcards.

        Args:
            data_root: Directory containing the files
            pivot_file_pattern: Pattern for pivot files (e.g., "GT_*.md")
            target_file_pattern: Pattern for target files (e.g., "pred_*.md")
            raise_on_missing: If True, raise FileNotFoundError when target file is missing

        Returns:
            List of FileEntryInfo objects containing matched file pairs

        Raises:
            ValueError: If patterns don't contain exactly one '*' wildcard
            FileNotFoundError: If raise_on_missing=True and a target file is missing
        """
        matches: list[FileEntryInfo] = []

        # Validate patterns contain exactly one wildcard
        if pivot_file_pattern.count("*") != 1 or target_file_pattern.count("*") != 1:
            raise ValueError("Patterns must contain exactly one '*' wildcard")

        # Extract prefix and suffix from patterns
        pivot_prefix, pivot_suffix = pivot_file_pattern.split("*", 1)
        target_prefix, target_suffix = target_file_pattern.split("*", 1)

        # Find all pivot files
        pivot_files = sorted(data_root.glob(pivot_file_pattern))

        for pivot_file in pivot_files:
            pivot_name = pivot_file.name

            # Extract the ID (the part that replaces the wildcard)
            file_id = pivot_name[
                len(pivot_prefix) : -len(pivot_suffix) if pivot_suffix else None
            ]

            # Construct target filename
            target_filename = f"{target_prefix}{file_id}{target_suffix}"
            target_file = data_root / target_filename

            # Only add to matches if target file exists
            if target_file.exists():
                entry_info = FileEntryInfo(
                    id=file_id, pivot_filename=pivot_file, target_filename=target_file
                )
                matches.append(entry_info)
            else:
                error_msg = (
                    f"No matching target file found for {pivot_file.name}: "
                    f"expected {target_filename}"
                )
                if raise_on_missing:
                    raise FileNotFoundError(error_msg)
                _log.warning(error_msg)

        _log.info(f"Found {len(matches)} matching file pairs")
        return matches
