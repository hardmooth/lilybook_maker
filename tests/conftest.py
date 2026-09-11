# -*- coding: utf-8 -*-
"""
pytest fixtures shared by all tests
"""
import os
import shutil
import sys

import pytest

MAKER_DIR = os.path.dirname( os.path.dirname( os.path.abspath( __file__)))
DATA_DIR  = os.path.join( os.path.dirname( os.path.abspath( __file__)), "data")

# make base.py, create_pdf.py, ... importable
if MAKER_DIR not in sys.path:
    sys.path.insert( 0, MAKER_DIR)


def tool_available( *tools):
    return all( shutil.which( tool) for tool in tools)

#: marker for tests that need the full toolchain (lilypond-book + pdflatex)
requires_toolchain = pytest.mark.skipif(
    not tool_available( "lilypond", "lilypond-book", "pdflatex"),
    reason = "lilypond, lilypond-book and pdflatex are required")


@pytest.fixture
def minimal_book( tmp_path):
    """A copy of the minimal example book in a temporary directory (returns its path)."""
    book_dir = tmp_path / "minimal_book"
    shutil.copytree( os.path.join( DATA_DIR, "minimal_book"), book_dir)
    return book_dir


@pytest.fixture
def maker_dir():
    return MAKER_DIR
