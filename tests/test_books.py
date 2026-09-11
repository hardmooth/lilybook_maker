# -*- coding: utf-8 -*-
"""
Integration tests: build real books (lilybook_template snapshot, liederbuch_advent_weihnachten, ...)
with all command line options of create_pdf.py. See lilybook_maker issue #4.

The books are taken from the LILYBOOK_BOOKS environment variable (os.pathsep separated directories)
or, if unset, from tests/data/template_book and the sibling directories of lilybook_maker. A book is
skipped if it is not present or its LaTeX packages are not installed.

Every build must exit with 0, produce the PDF and log no errors. Building a book takes a while,
so the default build is done once per book (fixture `default_build`) and inspected by several tests.
"""
import glob
import os

import pytest

from conftest import run_create_pdf, pdf_page_count

from base import EXIT_OK


def lytex_name( book):
    """base name of the book's single .lytex file, e.g. 'document'"""
    [lytex] = glob.glob( str( book / "*.lytex"))
    return os.path.splitext( os.path.basename( lytex))[0]


def assert_no_errors( result, book):
    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "LaTeX reported" not in result.stdout

    log = (book / "create_pdf.log").read_text( encoding = "utf-8", errors = "replace")
    error_lines = [ line for line in log.splitlines() if "[ERROR]" in line or "[CRITICAL]" in line]
    assert not error_lines, "errors logged:\n" + "\n".join( error_lines)


@pytest.fixture( scope = "module")
def default_build( book):
    """the book after a plain `create_pdf.py` call (lytex file and include directories auto-detected)"""
    result = run_create_pdf( book)
    assert_no_errors( result, book)
    return result


def test_check_option_passes( book):
    result = run_create_pdf( book, "--check")

    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "FAILED" not in result.stdout


def test_default_build_detects_lytex_file( book, default_build):
    assert "Detected '{}.lytex'".format( lytex_name( book)) in default_build.stdout


def test_default_build_writes_pdf_with_a_page_per_song( book, default_build):
    songs = [ s for s in glob.glob( str( book / "scores" / "*.ly"))
              if not os.path.basename( s).startswith( ("_", "default", "LY-include"))]

    assert pdf_page_count( book / (lytex_name( book) + ".pdf")) >= len( songs)


def test_default_build_replaces_lilypondfile_commands_with_snippets( book, default_build):
    tex = (book / "out" / (lytex_name( book) + ".tex")).read_text( encoding = "utf-8", errors = "replace")

    assert "\\lilypondfile" not in tex
    assert "lilypond" in tex.lower()


def test_all_long_options_full_rebuild_into_custom_out_dir_with_booklet( book):
    name = lytex_name( book)

    result = run_create_pdf( book, "--lytex", name + ".lytex", "--include=scores,inc", "--out", "build_long",
                             "--full", "--booklet", "--strict")

    assert_no_errors( result, book)
    assert (book / "build_long" / (name + ".pdf")).exists()
    n_pages  = pdf_page_count( book / (name + ".pdf"))
    n_padded = n_pages + (-n_pages % 4)
    assert pdf_page_count( book / (name + "-booklet.pdf")) == n_padded // 2


def test_all_short_options_incremental_build_keeps_out_dir( book, default_build):
    name  = lytex_name( book)
    stale = book / "out" / "stale_marker.txt"
    stale.write_text( "kept on incremental builds")

    result = run_create_pdf( book, "-L", name + ".lytex", "-I", "scores,inc", "-o", "out", "-b", "-s")

    assert_no_errors( result, book)
    assert (book / (name + "-booklet.pdf")).exists()
    assert stale.exists()
