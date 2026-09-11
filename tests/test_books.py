# -*- coding: utf-8 -*-
"""
Integration tests: build real books (lilybook_template, liederbuch_advent_weihnachten, ...) with all
command line options of create_pdf.py. See lilybook_maker issue #4.

The books are taken from the LILYBOOK_BOOKS environment variable (os.pathsep separated directories)
or, if unset, from the sibling directories of lilybook_maker. A book is skipped if it is not present
or its LaTeX packages are not installed.

    Every build must
      * exit with 0
      * produce the PDF
      * log no errors
"""
import glob
import os

from conftest import run_create_pdf, pdf_page_count

from base import EXIT_OK


def lytex_file( book):
    [lytex] = glob.glob( str( book / "*.lytex"))
    return os.path.basename( lytex)


def assert_clean_build( result, book, pdf_name, min_pages = 2):
    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "UNCAUGHT EXCEPTION" not in result.stdout
    assert "LaTeX reported" not in result.stdout

    log = (book / "create_pdf.log").read_text( encoding = "utf-8", errors = "replace")
    error_lines = [ line for line in log.splitlines() if "[ERROR]" in line or "[CRITICAL]" in line]
    assert not error_lines, "errors logged:\n" + "\n".join( error_lines)

    pdf = book / pdf_name
    assert pdf.exists(), "no PDF generated:\n" + result.stdout
    assert pdf_page_count( pdf) >= min_pages


def test_check( book):
    result = run_create_pdf( book, "--check")
    assert result.returncode == EXIT_OK, result.stdout + result.stderr
    assert "FAILED" not in result.stdout


def test_build_defaults( book):
    """plain call: lytex file and include directories (inc, scores, .) are auto-detected"""
    result = run_create_pdf( book)
    name = os.path.splitext( lytex_file( book))[0]
    assert "Detected '{}.lytex'".format( name) in result.stdout
    assert_clean_build( result, book, name + ".pdf")
    assert (book / "out" / (name + ".tex")).exists()


def test_build_all_long_options( book):
    """all options in their long form, custom output directory, full rebuild with booklet in strict mode"""
    lytex = lytex_file( book)
    name  = os.path.splitext( lytex)[0]
    result = run_create_pdf( book, "--lytex", lytex, "--include=scores,inc", "--out", "build_long",
                             "--full", "--booklet", "--strict")
    assert_clean_build( result, book, name + ".pdf")

    assert (book / "build_long" / (name + ".tex")).exists()
    assert (book / "build_long" / (name + ".pdf")).exists()

    booklet = book / (name + "-booklet.pdf")
    assert booklet.exists(), result.stdout
    n_pages = pdf_page_count( book / (name + ".pdf"))
    assert pdf_page_count( booklet) == (n_pages + (-n_pages % 4)) // 2


def test_build_all_short_options( book):
    """all options in their short form; incremental build into the default out/ of test_build_defaults"""
    lytex = lytex_file( book)
    name  = os.path.splitext( lytex)[0]
    stale = book / "out" / "stale_marker.txt"
    stale.parent.mkdir( exist_ok = True)
    stale.write_text( "kept on incremental builds")

    result = run_create_pdf( book, "-L", lytex, "-I", "scores,inc", "-o", "out", "-b", "-s")
    assert_clean_build( result, book, name + ".pdf")
    assert (book / (name + "-booklet.pdf")).exists()
    # no -F/--full: out/ was not cleaned
    assert stale.exists()

    result = run_create_pdf( book, "-F", "-L", lytex)
    assert_clean_build( result, book, name + ".pdf")
    assert not stale.exists()


def test_build_pdf_reflects_book_content( book):
    """the generated tex contains the lilypond snippets and the PDF has a sensible number of pages"""
    name = os.path.splitext( lytex_file( book))[0]
    tex = (book / "out" / (name + ".tex")).read_text( encoding = "utf-8", errors = "replace")
    assert "\\lilypondfile" not in tex, "lilypond-book left \\lilypondfile commands in the tex file"
    assert "lilypond" in tex.lower()

    scores = glob.glob( str( book / "scores" / "*.ly"))
    songs  = [ s for s in scores if not os.path.basename( s).startswith( ("_", "default", "LY-include"))]
    # at least one page per song
    assert pdf_page_count( book / (name + ".pdf")) >= len( songs)
