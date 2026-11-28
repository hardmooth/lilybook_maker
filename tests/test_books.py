# -*- coding: utf-8 -*-
"""
Integration tests: build real books (template snapshot, liederbuch, Kommersbuch, ...) with every
lilybook target. See lilybook_maker issue #4.

The books are taken from the LILYBOOK_BOOKS environment variable (os.pathsep separated directories)
or, if unset, from tests/data/template_book and the sibling directories of lilybook_maker. A book is
skipped if it is not present or its LaTeX packages are not installed.

Every build must exit with 0, produce the PDF and report no LaTeX errors. Building a book takes a
while, so the default build is done once per book (fixture `default_build`) and inspected by several tests.
"""
import glob
import os
import re

import pytest

from conftest import requires_pdfpages, run_lilybook, pdf_pages


def lytex_name( book):
    [lytex] = glob.glob( str( book / "*.lytex"))
    return os.path.splitext( os.path.basename( lytex))[0]


def assert_clean( result):
    assert result.returncode == 0, result.stdout
    assert "LaTeX errors" not in result.stdout, result.stdout
    assert "MISSING" not in result.stdout, result.stdout


@pytest.fixture( scope = "module")
def default_build( book):
    """the book after a plain `lilybook` call"""
    result = run_lilybook( book)
    assert_clean( result)
    return result


def test_check_passes( book):
    result = run_lilybook( book, "check")

    assert_clean( result)


def test_default_build_writes_pdf_with_a_page_per_song( book, default_build):
    songs = [ s for s in glob.glob( str( book / "scores" / "*.ly"))
              if not os.path.basename( s).startswith( ("_", "default", "LY-include"))]

    assert len( pdf_pages( book / (lytex_name( book) + ".pdf"))) >= len( songs)


def test_default_build_replaces_lilypondfile_commands_with_snippets( book, default_build):
    tex = (book / "out" / (lytex_name( book) + ".tex")).read_text( encoding = "utf-8", errors = "replace")

    # a book may still mention \\lilypondfile in a comment
    assert not re.search( r"^[^%\n]*\\lilypondfile", tex, re.MULTILINE)
    assert "lilypond" in tex.lower()


def test_default_build_detects_textwidth( book, default_build):
    assert "cannot detect textwidth" not in default_build.stdout, default_build.stdout
    # the LaTeX run of that detection writes tmp*.pdf and the like into the current directory
    assert not glob.glob( str( book / "tmp*")), "leftovers of the textwidth detection"


def test_rebuild_without_changes_does_nothing( book, default_build):
    result = run_lilybook( book)

    assert_clean( result)
    assert "lilypond-book" not in result.stdout
    assert "latexmk" not in result.stdout


@requires_pdfpages
def test_booklet_has_two_pages_per_landscape_sheet( book, default_build):
    result = run_lilybook( book, "booklet")

    assert_clean( result)
    n_pages = len( pdf_pages( book / (lytex_name( book) + ".pdf")))
    sheets  = pdf_pages( book / (lytex_name( book) + "-booklet.pdf"))
    assert len( sheets) == (n_pages + (-n_pages % 4)) // 2
    assert all( w > h for w, h in sheets)


def test_strict_full_rebuild_passes( book):
    result = run_lilybook( book, "full", "STRICT=1")

    assert_clean( result)
    assert (book / (lytex_name( book) + ".pdf")).exists()
