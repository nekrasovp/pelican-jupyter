import importlib

import pytest

from pelican.plugins import ipynb_reader


def test_reader_receiver_registers_current_class():
    class Readers:
        reader_classes = {}

    readers = Readers()
    ipynb_reader.add_reader(readers)

    assert readers.reader_classes["ipynb"] is ipynb_reader.IPYNBReader


def test_legacy_markup_is_only_a_deprecated_reexport():
    with pytest.warns(DeprecationWarning, match="pelican.plugins.ipynb_reader"):
        legacy = importlib.reload(importlib.import_module("pelican_jupyter.markup"))

    assert legacy.IPYNBReader is ipynb_reader.IPYNBReader
    assert legacy.IPythonNB is ipynb_reader.IPYNBReader
