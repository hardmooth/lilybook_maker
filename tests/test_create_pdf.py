# -*- coding: utf-8 -*-
"""
tests for create_pdf.py

The integration tests build the minimal example book in tests/data/minimal_book and thus require
lilypond, lilypond-book and pdflatex to be installed. They are skipped otherwise.
"""
import os

import pytest

from conftest import requires_toolchain, run_create_pdf, pdf_page_count

import create_pdf
from base import EXIT_OK, EXIT_BAD_PARAMETERS, EXIT_BAD_PREREQUISITES


# ------------------------------------------------------------------------------------------------
# unit tests

def test_check_py_requirement_installed():
    assert create_pdf._CheckPyRequirement( "pytest") is None


def test_check_py_requirement_missing():
    error = create_pdf._CheckPyRequirement( "surely_not_installed_package_xyz")
    assert error and "not found" in error


def test_check_py_requirement_version_constraint():
    assert create_pdf._CheckPyRequirement( "pytest>=1.0") is None
    error = create_pdf._CheckPyRequirement( "pytest<0.1")
    # only verifiable if 'packaging' is available
    try:
        import packaging  # noqa: F401
        assert error and "required" in error
    except ImportError:
        assert error is None


def test_check_encoding_detects_non_utf8( tmp_path):
    (tmp_path / "ok.tex").write_text( "äöü", encoding = "utf-8")
    assert create_pdf.CheckEncoding( str( tmp_path)) is True

    (tmp_path / "bad.ly").write_bytes( "äöü".encode( "latin-1"))
    assert create_pdf.CheckEncoding( str( tmp_path)) is False

    # files not matching the patterns are ignored
    (tmp_path / "bad.ly").unlink()
    (tmp_path / "bad.txt").write_bytes( "äöü".encode( "latin-1"))
    assert create_pdf.CheckEncoding( str( tmp_path)) is True


def test_lilypond_book_command_is_a_list():
    assert isinstance( create_pdf.CMD_LILYPOND, list)
    assert create_pdf.CMD_LILYPOND
    assert os.path.basename( create_pdf.CMD_LILYPOND[-1]).startswith( "lilypond-book")


def test_log_file_pattern_matches_absolute_paths():
    pat = create_pdf.LOG_FILE_PATTERN
    assert pat.search( r"see C:\Users\me\out\book.log for details").group() == r"C:\Users\me\out\book.log"
    assert pat.search( "see /home/me/out/book.log for details").group() == "/home/me/out/book.log"
    assert pat.search( "relative out/book.log") is None


# ------------------------------------------------------------------------------------------------
# integration tests

@requires_toolchain
def test_check_prerequisites( minimal_book):
    result = run_create_pdf( minimal_book, "--check")
    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "Checking prerequisites" in result.stdout
    assert "FAILED" not in result.stdout


@requires_toolchain
def test_build_minimal_book( minimal_book):
    result = run_create_pdf( minimal_book, "--include=scores,inc", "minimal_book.lytex")
    assert result.returncode == EXIT_OK, result.stdout + result.stderr

    pdf = minimal_book / "minimal_book.pdf"
    assert pdf.exists(), "no PDF generated:\n" + result.stdout
    assert pdf_page_count( pdf) >= 4

    # lilypond-book output and LaTeX intermediates are in out/
    assert (minimal_book / "out" / "minimal_book.tex").exists()
    assert (minimal_book / "out" / "minimal_book.pdf").exists()
    # index was created (preamble has \makeindex, book has \index and \printindex)
    assert (minimal_book / "out" / "minimal_book.ind").exists()
    # the log file lives in the book directory
    assert (minimal_book / "create_pdf.log").exists()

    # the generated tex must contain the lilypond snippets
    tex = (minimal_book / "out" / "minimal_book.tex").read_text( encoding = "utf-8")
    assert "lilypond" in tex.lower()
    assert "\\lilypondfile" not in tex

    # no LaTeX errors
    assert "LaTeX reported" not in result.stdout
    assert "UNCAUGHT EXCEPTION" not in result.stdout


@requires_toolchain
def test_build_detects_lytex_and_default_includes( minimal_book):
    # no lytex file and no include dirs given: the single *.lytex and the inc/scores dirs are detected
    result = run_create_pdf( minimal_book)
    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "Detected 'minimal_book.lytex'" in result.stdout
    assert (minimal_book / "minimal_book.pdf").exists()


@requires_toolchain
def test_build_with_booklet( minimal_book):
    result = run_create_pdf( minimal_book, "--booklet", "minimal_book.lytex")
    assert result.returncode == EXIT_OK, result.stdout + result.stderr

    pdf     = minimal_book / "minimal_book.pdf"
    booklet = minimal_book / "minimal_book-booklet.pdf"
    assert booklet.exists(), result.stdout

    n_pages = pdf_page_count( pdf)
    # booklet: pages padded to a multiple of 4, two per sheet
    assert pdf_page_count( booklet) == (n_pages + (-n_pages % 4)) // 2


@requires_toolchain
def test_full_rebuild_cleans_out_dir( minimal_book):
    out_dir = minimal_book / "out"
    out_dir.mkdir()
    stale = out_dir / "stale.txt"
    stale.write_text( "old")

    result = run_create_pdf( minimal_book, "--full", "minimal_book.lytex")
    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert not stale.exists()
    assert (minimal_book / "minimal_book.pdf").exists()


@requires_toolchain
def test_strict_build_fails_on_latex_error( minimal_book):
    lytex = minimal_book / "minimal_book.lytex"
    lytex.write_text( lytex.read_text( encoding = "utf-8").replace( "Nur Text.", "\\undefinedcommand"), encoding = "utf-8")

    result = run_create_pdf( minimal_book, "--strict", "minimal_book.lytex")
    assert result.returncode != EXIT_OK
    assert "LaTeX reported" in result.stdout


@requires_toolchain
def test_strict_build_fails_on_invalid_encoding( minimal_book):
    (minimal_book / "inc" / "latin1.tex").write_bytes( "% äöü".encode( "latin-1"))

    result = run_create_pdf( minimal_book, "--strict", "minimal_book.lytex")
    assert result.returncode == EXIT_BAD_PREREQUISITES
    assert "Invalidly encoded file" in result.stdout
    assert not (minimal_book / "minimal_book.pdf").exists()


def test_no_lytex_file_fails( tmp_path):
    result = run_create_pdf( tmp_path)
    assert result.returncode in (EXIT_BAD_PARAMETERS, 2), result.stdout + result.stderr
