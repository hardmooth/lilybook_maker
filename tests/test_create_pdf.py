# -*- coding: utf-8 -*-
"""
tests for create_pdf.py

The integration tests build the minimal example book in tests/data/minimal_book and thus require
lilypond, lilypond-book and pdflatex to be installed. They are skipped otherwise.
"""
import os
import stat

import pytest

from conftest import requires_toolchain, run_create_pdf, pdf_page_count, copy_book, DATA_DIR

import create_pdf
from base import EXIT_OK, EXIT_BAD_PARAMETERS, EXIT_BAD_PREREQUISITES, IS_WINDOWS


# ------------------------------------------------------------------------------------------------
# pip requirement check

def test_installed_requirement_passes():
    assert create_pdf._CheckPyRequirement( "pytest") is None


def test_missing_requirement_is_reported_with_install_hint():
    error = create_pdf._CheckPyRequirement( "surely_not_installed_package_xyz")

    assert "not found" in error
    assert "pip install" in error


def test_satisfied_version_constraint_passes():
    assert create_pdf._CheckPyRequirement( "pytest>=1.0") is None


def test_violated_version_constraint_is_reported():
    error = create_pdf._CheckPyRequirement( "pytest<0.1")

    assert "required" in error


# ------------------------------------------------------------------------------------------------
# encoding check

def test_utf8_files_pass_encoding_check( tmp_path):
    (tmp_path / "ok.tex").write_text( "äöü", encoding = "utf-8")

    assert create_pdf.CheckEncoding( str( tmp_path)) is True


def test_latin1_score_fails_encoding_check( tmp_path):
    (tmp_path / "bad.ly").write_bytes( "äöü".encode( "latin-1"))

    assert create_pdf.CheckEncoding( str( tmp_path)) is False


def test_encoding_check_ignores_unrelated_file_types( tmp_path):
    (tmp_path / "notes.txt").write_bytes( "äöü".encode( "latin-1"))

    assert create_pdf.CheckEncoding( str( tmp_path)) is True


# ------------------------------------------------------------------------------------------------
# lilypond-book lookup

def _fake_lilypond_dir( tmp_path, book_name):
    """a directory with an executable 'lilypond' and a lilypond-book script (returns the dir)"""
    bin_dir = tmp_path / "lily" / "bin"
    bin_dir.mkdir( parents = True)
    lilypond = bin_dir / ("lilypond.exe" if IS_WINDOWS else "lilypond")
    lilypond.write_text( "")
    lilypond.chmod( lilypond.stat().st_mode | stat.S_IXUSR)
    (bin_dir / book_name).write_text( "")
    return bin_dir


def test_lilypond_book_py_is_found_next_to_lilypond_in_path( tmp_path, monkeypatch):
    bin_dir = _fake_lilypond_dir( tmp_path, "lilypond-book.py")
    monkeypatch.setenv( "PATH", str( bin_dir))
    monkeypatch.setattr( create_pdf, "PATH_LILYPOND", "")

    assert create_pdf._FindLilypondBook() == str( bin_dir / "lilypond-book.py")


def test_lilypond_book_is_found_in_configured_directory( tmp_path, monkeypatch):
    bin_dir = _fake_lilypond_dir( tmp_path, "lilypond-book")
    monkeypatch.setenv( "PATH", str( tmp_path))    # nothing useful in PATH
    monkeypatch.setattr( create_pdf, "PATH_LILYPOND", str( bin_dir))

    assert create_pdf._FindLilypondBook() == str( bin_dir / "lilypond-book")


def test_lilypond_book_lookup_returns_none_if_absent( tmp_path, monkeypatch):
    monkeypatch.setenv( "PATH", str( tmp_path))
    monkeypatch.setattr( create_pdf, "PATH_LILYPOND", "")

    assert create_pdf._FindLilypondBook() is None


# ------------------------------------------------------------------------------------------------
# log file detection

@pytest.mark.parametrize( "line, expected", [
    ( r"see C:\Users\me\out\book.log for details", r"C:\Users\me\out\book.log"),
    ( "see /home/me/out/book.log for details",     "/home/me/out/book.log"),
    ( "relative out/book.log",                     None),
])
def test_log_file_pattern_matches_only_absolute_paths( line, expected):
    match = create_pdf.LOG_FILE_PATTERN.search( line)

    assert (match.group() if match else None) == expected


# ------------------------------------------------------------------------------------------------
# integration tests on the minimal book

@pytest.fixture( scope = "module")
def built_minimal_book( tmp_path_factory):
    """the minimal book after one build with explicit include directories (shared by the read-only tests below)"""
    book = copy_book( os.path.join( DATA_DIR, "minimal_book"), tmp_path_factory.mktemp( "built") / "minimal_book")
    result = run_create_pdf( book, "--include=scores,inc", "minimal_book.lytex")
    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    return book, result


@requires_toolchain
def test_check_prerequisites_passes( minimal_book):
    result = run_create_pdf( minimal_book, "--check")

    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "FAILED" not in result.stdout


@requires_toolchain
def test_build_writes_pdf_next_to_lytex( built_minimal_book):
    book, _ = built_minimal_book

    assert pdf_page_count( book / "minimal_book.pdf") >= 4


@requires_toolchain
def test_build_keeps_intermediates_in_out_dir( built_minimal_book):
    book, _ = built_minimal_book

    assert (book / "out" / "minimal_book.tex").exists()
    assert (book / "out" / "minimal_book.pdf").exists()


@requires_toolchain
def test_build_creates_index_for_makeindex_books( built_minimal_book):
    book, _ = built_minimal_book

    assert (book / "out" / "minimal_book.ind").exists()


@requires_toolchain
def test_build_replaces_lilypondfile_commands_with_snippets( built_minimal_book):
    book, _ = built_minimal_book
    tex = (book / "out" / "minimal_book.tex").read_text( encoding = "utf-8")

    assert "\\lilypondfile" not in tex
    assert "lilypond" in tex.lower()


@requires_toolchain
def test_build_logs_no_errors( built_minimal_book):
    book, result = built_minimal_book
    log = (book / "create_pdf.log").read_text( encoding = "utf-8")

    assert "LaTeX reported" not in result.stdout
    assert "[ERROR]" not in log
    assert "[CRITICAL]" not in log


@requires_toolchain
def test_build_detects_single_lytex_and_default_include_dirs( minimal_book):
    result = run_create_pdf( minimal_book)

    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "Detected 'minimal_book.lytex'" in result.stdout
    assert (minimal_book / "minimal_book.pdf").exists()


@requires_toolchain
def test_booklet_option_writes_booklet_with_two_pages_per_sheet( minimal_book):
    result = run_create_pdf( minimal_book, "--booklet", "minimal_book.lytex")
    assert result.returncode == EXIT_OK, result.stdout + result.stderr

    n_pages   = pdf_page_count( minimal_book / "minimal_book.pdf")
    n_padded  = n_pages + (-n_pages % 4)
    assert pdf_page_count( minimal_book / "minimal_book-booklet.pdf") == n_padded // 2


@requires_toolchain
def test_full_option_cleans_out_dir_before_building( minimal_book):
    stale = minimal_book / "out" / "stale.txt"
    stale.parent.mkdir()
    stale.write_text( "old")

    result = run_create_pdf( minimal_book, "--full", "minimal_book.lytex")

    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert not stale.exists()


@requires_toolchain
def test_strict_option_fails_on_latex_error( minimal_book):
    lytex = minimal_book / "minimal_book.lytex"
    lytex.write_text( lytex.read_text( encoding = "utf-8").replace( "Nur Text.", "\\undefinedcommand"), encoding = "utf-8")

    result = run_create_pdf( minimal_book, "--strict", "minimal_book.lytex")

    assert result.returncode != EXIT_OK
    assert "LaTeX reported" in result.stdout


@requires_toolchain
def test_strict_option_fails_on_invalid_encoding_before_building( minimal_book):
    (minimal_book / "inc" / "latin1.tex").write_bytes( "% äöü".encode( "latin-1"))

    result = run_create_pdf( minimal_book, "--strict", "minimal_book.lytex")

    assert result.returncode == EXIT_BAD_PREREQUISITES
    assert "Invalidly encoded file" in result.stdout
    assert not (minimal_book / "minimal_book.pdf").exists()


@requires_toolchain
def test_missing_lytex_file_is_a_parameter_error( tmp_path):
    result = run_create_pdf( tmp_path)

    assert result.returncode == EXIT_BAD_PARAMETERS, result.stdout + result.stderr
    assert "no input file specified" in result.stdout
