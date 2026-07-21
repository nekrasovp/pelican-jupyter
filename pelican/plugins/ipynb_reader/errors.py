"""Structured failures for the direct notebook reader."""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class ReaderStage(str, Enum):
    """Stable stages exposed to publishers and tests."""

    METADATA_DISCOVERY = "metadata_discovery"
    METADATA_PARSING = "metadata_parsing"
    VALIDATION = "validation"
    NOTEBOOK_PARSING = "notebook_parsing"
    CONVERSION = "conversion"
    COPY = "copy"
    PUBLICATION_VERIFICATION = "publication_verification"


class NotebookReaderError(Exception):
    """Base class for deterministic, source-aware reader failures."""

    stage: ReaderStage

    def __init__(  # noqa: B042 - structured attributes define the public contract
        self,
        source_path: str | Path,
        category: str,
        cause_message: str,
        *,
        cause_type: str | None = None,
    ) -> None:
        self.source_path = str(source_path)
        self.category = category
        self.cause_type = cause_type or category
        self.cause_message = cause_message
        super().__init__(
            f"{self.source_path}: {self.stage.value}: {self.category} "
            f"[{self.cause_type}]: {self.cause_message}"
        )

    @classmethod
    def from_cause(
        cls,
        source_path: str | Path,
        category: str,
        cause: BaseException,
    ) -> "NotebookReaderError":
        root = cause
        while root.__cause__ is not None:
            root = root.__cause__
        return cls(
            source_path,
            category,
            str(root) or repr(root),
            cause_type=type(root).__name__,
        )


class MetadataDiscoveryError(NotebookReaderError):
    stage = ReaderStage.METADATA_DISCOVERY


class MetadataParsingError(NotebookReaderError):
    stage = ReaderStage.METADATA_PARSING


class MetadataValidationError(NotebookReaderError):
    stage = ReaderStage.VALIDATION


class NotebookParsingError(NotebookReaderError):
    stage = ReaderStage.NOTEBOOK_PARSING


class NotebookConversionError(NotebookReaderError):
    stage = ReaderStage.CONVERSION


class NotebookCopyError(NotebookReaderError):
    stage = ReaderStage.COPY


class NotebookPublicationError(NotebookReaderError):
    """Reserved for the independent expected-route gate owned by PLUGIN-003."""

    stage = ReaderStage.PUBLICATION_VERIFICATION
