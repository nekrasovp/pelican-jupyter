"""Deprecated import path for the namespace-owned direct reader.

Use :mod:`pelican.plugins.ipynb_reader`. This module intentionally contains no
reader, metadata, conversion, first-cell, or Liquid-tag implementation.
"""

import warnings

warnings.warn(
    "pelican_jupyter.markup is deprecated; use pelican.plugins.ipynb_reader",
    DeprecationWarning,
    stacklevel=2,
)

from pelican.plugins.ipynb_reader import (  # noqa: E402,F401
    HTML_CONTRACT_VERSION,
    IPYNBReader,
    IPythonNB,
    NotebookMetadata,
    NotebookReaderError,
    add_reader,
    register,
)

__all__ = [
    "HTML_CONTRACT_VERSION",
    "IPYNBReader",
    "IPythonNB",
    "NotebookMetadata",
    "NotebookReaderError",
    "add_reader",
    "register",
]
