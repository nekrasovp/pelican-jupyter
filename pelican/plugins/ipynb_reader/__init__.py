"""Direct, static ``.ipynb + .nbdata`` reader for Pelican 4."""

from typing import Any

from pelican.plugins import signals  # type: ignore[attr-defined]

from .conversion import HTML_CONTRACT_VERSION, convert_notebook_fragment
from .errors import (
    MetadataDiscoveryError,
    MetadataParsingError,
    MetadataValidationError,
    NotebookConversionError,
    NotebookCopyError,
    NotebookParsingError,
    NotebookPublicationError,
    NotebookReaderError,
    ReaderStage,
)
from .reader import IPYNBReader, IPythonNB, NotebookMetadata


def add_reader(readers: Any) -> None:
    """Register the current reader through Pelican's readers_init signal."""

    readers.reader_classes["ipynb"] = IPYNBReader


def register() -> None:
    signals.readers_init.connect(add_reader)


__all__ = [
    "HTML_CONTRACT_VERSION",
    "IPYNBReader",
    "IPythonNB",
    "MetadataDiscoveryError",
    "MetadataParsingError",
    "MetadataValidationError",
    "NotebookConversionError",
    "NotebookCopyError",
    "NotebookMetadata",
    "NotebookParsingError",
    "NotebookPublicationError",
    "NotebookReaderError",
    "ReaderStage",
    "add_reader",
    "convert_notebook_fragment",
    "register",
]
