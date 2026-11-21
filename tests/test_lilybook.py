# -*- coding: utf-8 -*-
"""
tests for lilybook / lilybook.mk on the minimal example book (tests/data/minimal_book)
"""
import os
import subprocess

import pytest

from conftest import requires_toolchain, requires_pdfpages, run_lilybook, pdf_pages, copy_book, DATA_DIR

pytestmark = requires_toolchain

BOOK = "minimal_book"


def assert_ok( result):
    assert result.returncode == 0, result.stdout


def assert_no_latex_errors( result):
    assert "LaTeX errors" not in result.stdout, result.stdout


# ------------------------------------------------------------------------------------------------
# detection and checks

def test_help_shows_detected_book_and_include_dirs( minimal_book):
    result = run_lilybook( minimal_book, "help")

    assert_ok( result)
    assert "book: minimal_book" in result.stdout
    assert "includes: inc scores ." in result.stdout


def test_check_passes_on_minimal_book( minimal_book):
    result = run_lilybook( minimal_book, "check")

    assert_ok( result)
    assert "MISSING" not in result.stdout
    assert "LaTeX packages" in result.stdout


def test_check_runs_the_books_check_py( minimal_book):
    (minimal_book / "check.py").write_text( "print('CHECK_PY_MARKER')\n")

    result = run_lilybook( minimal_book, "check")

    assert_ok( result)
    assert "CHECK_PY_MARKER" in result.stdout


def test_missing_lytex_file_is_reported( tmp_path):
    result = run_lilybook( tmp_path, "pdf")

    assert result.returncode != 0
    assert "expected exactly one .lytex file" in result.stdout
    assert "found: none" in result.stdout


def test_ambiguous_lytex_files_are_reported( minimal_book):
    (minimal_book / "second.lytex").write_text( "")

    result = run_lilybook( minimal_book, "pdf")

    assert result.returncode != 0
    assert "second.lytex" in result.stdout


def test_non_utf8_source_stops_the_build( minimal_book):
    (minimal_book / "inc" / "latin1.tex").write_bytes( "% äöü".encode( "latin-1"))

    result = run_lilybook( minimal_book, "pdf")

    assert result.returncode != 0
    assert "NOT UTF-8" in result.stdout
    assert "inc/latin1.tex" in result.stdout
    assert not (minimal_book / (BOOK + ".pdf")).exists()


def test_source_file_with_a_space_in_its_name_is_ignored_with_a_warning( minimal_book):
    (minimal_book / "scores" / "alle_meine_entchen - Kopie.ly").write_text( "{ c' }\n")

    result = run_lilybook( minimal_book, "pdf")

    assert_ok( result)
    assert 'ignoring files with a space in their name: "scores/alle_meine_entchen - Kopie.ly"' in result.stdout
    assert (minimal_book / (BOOK + ".pdf")).exists()


def test_stray_pdfs_next_to_the_scores_do_not_disturb_the_build( minimal_book):
    # as left behind by an editor on Windows: a PDF of a single score and a copy with a space in its name
    stale = minimal_book / "scores" / "alle_meine_entchen.pdf"
    stale.write_bytes( b"not a pdf")
    (minimal_book / "scores" / "alle_meine_entchen - Kopie.pdf").write_bytes( b"not a pdf")

    result = run_lilybook( minimal_book, "pdf")

    assert_ok( result)
    assert "==       lilypond scores/" not in result.stdout
    assert stale.read_bytes() == b"not a pdf"


# ------------------------------------------------------------------------------------------------
# the default build, done once and inspected by several tests

@pytest.fixture( scope = "module")
def built( tmp_path_factory):
    book = copy_book( os.path.join( DATA_DIR, "minimal_book"), tmp_path_factory.mktemp( "built") / BOOK)
    result = run_lilybook( book)
    assert_ok( result)
    return book, result


def test_default_target_writes_pdf_next_to_lytex( built):
    book, _ = built

    assert len( pdf_pages( book / (BOOK + ".pdf"))) >= 4


def test_build_keeps_intermediates_in_out_dir( built):
    book, _ = built

    assert (book / "out" / (BOOK + ".tex")).exists()
    assert (book / "out" / (BOOK + ".pdf")).exists()


def test_build_runs_makeindex_for_books_with_an_index( built):
    book, _ = built

    assert (book / "out" / (BOOK + ".ind")).exists()


def test_build_replaces_lilypondfile_commands_with_snippets( built):
    book, _ = built
    tex = (book / "out" / (BOOK + ".tex")).read_text( encoding = "utf-8")

    assert "\\lilypondfile" not in tex
    assert "lilypond" in tex.lower()


def test_build_reports_no_latex_errors( built):
    _, result = built

    assert_no_latex_errors( result)


def test_build_writes_lilybook_log( built):
    book, result = built

    assert (book / "lilybook.log").read_text( encoding = "utf-8", errors = "replace").strip() == result.stdout.strip()


def test_rebuild_without_changes_does_nothing( built):
    book, _ = built

    result = run_lilybook( book)

    assert_ok( result)
    assert "lilypond-book" not in result.stdout
    assert "latexmk" not in result.stdout


# ------------------------------------------------------------------------------------------------
# incremental builds

def test_changed_score_reruns_lilypond_book_and_latex( minimal_book):
    assert_ok( run_lilybook( minimal_book))
    score = minimal_book / "scores" / "alle_meine_entchen.ly"
    score.write_text( score.read_text( encoding = "utf-8").replace( "Al -- le", "AL -- LE"), encoding = "utf-8")

    result = run_lilybook( minimal_book)

    assert_ok( result)
    assert "lilypond-book" in result.stdout
    assert "latexmk" in result.stdout


def test_changed_included_ly_file_discards_cached_snippets( minimal_book):
    assert_ok( run_lilybook( minimal_book))
    snippet_dirs_before = { p.name: p.stat().st_mtime for p in (minimal_book / "out").iterdir() if p.is_dir() and len( p.name) == 2}
    assert snippet_dirs_before, "expected lilypond-book snippet directories in out/"
    layout = minimal_book / "scores" / "default.ly"
    layout.write_text( layout.read_text( encoding = "utf-8").replace( "staff-size 16", "staff-size 20"), encoding = "utf-8")

    result = run_lilybook( minimal_book)

    assert_ok( result)
    assert "discarding cached snippets" in result.stdout
    snippet_dirs_after = { p.name: p.stat().st_mtime for p in (minimal_book / "out").iterdir() if p.is_dir() and len( p.name) == 2}
    assert all( snippet_dirs_after[name] > mtime for name, mtime in snippet_dirs_before.items() if name in snippet_dirs_after)


def test_changed_tex_include_reruns_the_build( minimal_book):
    assert_ok( run_lilybook( minimal_book))
    preamble = minimal_book / "inc" / "preamble.tex"
    preamble.write_text( preamble.read_text( encoding = "utf-8").replace( "Hallo aus", "Servus aus"), encoding = "utf-8")

    result = run_lilybook( minimal_book)

    assert_ok( result)
    assert "latexmk" in result.stdout


# ------------------------------------------------------------------------------------------------
# targets and variables

@requires_pdfpages
def test_booklet_target_writes_landscape_sheets_with_two_pages_each( minimal_book):
    result = run_lilybook( minimal_book, "booklet")

    assert_ok( result)
    pages  = pdf_pages( minimal_book / (BOOK + ".pdf"))
    sheets = pdf_pages( minimal_book / (BOOK + "-booklet.pdf"))
    n_padded = len( pages) + (-len( pages) % 4)
    assert len( sheets) == n_padded // 2
    assert all( w > h for w, h in sheets)


def test_scores_target_writes_a_pdf_per_score_but_skips_templates( minimal_book):
    score = minimal_book / "scores" / "alle_meine_entchen.ly"
    (minimal_book / "scores" / "_template.ly").write_text( score.read_text( encoding = "utf-8"), encoding = "utf-8")

    result = run_lilybook( minimal_book, "scores")

    assert_ok( result)
    assert (minimal_book / "scores" / "alle_meine_entchen.pdf").exists()
    assert not (minimal_book / "scores" / "_template.pdf").exists()
    assert not (minimal_book / "scores" / "default.pdf").exists()


def test_out_variable_moves_intermediates( minimal_book):
    result = run_lilybook( minimal_book, "pdf", "OUT=build_x")

    assert_ok( result)
    assert (minimal_book / "build_x" / (BOOK + ".pdf")).exists()
    assert not (minimal_book / "out").exists()


def test_book_mk_overrides_settings( minimal_book):
    (minimal_book / "book.mk").write_text( "OUT := build_from_book_mk\n")

    result = run_lilybook( minimal_book)

    assert_ok( result)
    assert (minimal_book / "build_from_book_mk" / (BOOK + ".pdf")).exists()


def test_clean_removes_out_dir_and_pdfs( minimal_book):
    assert_ok( run_lilybook( minimal_book, "scores"))
    assert_ok( run_lilybook( minimal_book))

    result = run_lilybook( minimal_book, "clean")

    assert_ok( result)
    assert not (minimal_book / "out").exists()
    assert not (minimal_book / (BOOK + ".pdf")).exists()
    assert not (minimal_book / "scores" / "alle_meine_entchen.pdf").exists()


def test_full_target_rebuilds_from_scratch( minimal_book):
    assert_ok( run_lilybook( minimal_book))
    stale = minimal_book / "out" / "stale.txt"
    stale.write_text( "old")

    result = run_lilybook( minimal_book, "full")

    assert_ok( result)
    assert not stale.exists()
    assert (minimal_book / (BOOK + ".pdf")).exists()


def test_gitshort_is_written_only_if_the_sources_use_it( minimal_book):
    assert_ok( run_lilybook( minimal_book))
    assert not (minimal_book / "_gitshort").exists()

    preamble = minimal_book / "inc" / "preamble.tex"
    preamble.write_text( preamble.read_text( encoding = "utf-8") + "\\newcommand{\\buildhash}{\\IfFileExists{_gitshort}{\\input{_gitshort}}{unknown}}\n", encoding = "utf-8")
    result = run_lilybook( minimal_book)

    assert_ok( result)
    # the temporary book is no git repository itself, but pytest may place it inside one (--basetemp in CI)
    git = subprocess.run( [ "git", "rev-parse", "--short", "HEAD"], cwd = str( minimal_book), capture_output = True, text = True)
    expected = git.stdout.strip() if git.returncode == 0 else "unknown"
    assert (minimal_book / "_gitshort").read_text().strip() == expected


# ------------------------------------------------------------------------------------------------
# LaTeX errors

def _break_latex( book):
    lytex = book / (BOOK + ".lytex")
    lytex.write_text( lytex.read_text( encoding = "utf-8").replace( "Nur Text.", "\\undefinedcommand"), encoding = "utf-8")


def test_latex_error_is_reported_but_pdf_is_still_written_by_default( minimal_book):
    _break_latex( minimal_book)

    result = run_lilybook( minimal_book)

    assert_ok( result)
    assert "LaTeX errors" in result.stdout
    assert "! Undefined control sequence." in result.stdout
    assert (minimal_book / (BOOK + ".pdf")).exists()


def test_strict_fails_on_latex_error( minimal_book):
    _break_latex( minimal_book)

    result = run_lilybook( minimal_book, "STRICT=1")

    assert result.returncode != 0
    assert "! Undefined control sequence." in result.stdout
    assert not (minimal_book / (BOOK + ".pdf")).exists()
