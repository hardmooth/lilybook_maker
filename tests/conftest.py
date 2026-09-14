# -*- coding: utf-8 -*-
"""
pytest fixtures and helpers shared by all tests.

The tests drive the `lilybook` wrapper (and thus lilybook.mk) as a subprocess inside a temporary
copy of a book and assert on the produced files and output.
"""
import os
import shutil
import subprocess
import sys

import pytest

MAKER_DIR = os.path.dirname( os.path.dirname( os.path.abspath( __file__)))
DATA_DIR  = os.path.join( os.path.dirname( os.path.abspath( __file__)), "data")
LILYBOOK  = os.path.join( MAKER_DIR, "lilybook")
MAKEFILE  = os.path.join( MAKER_DIR, "lilybook.mk")

if sys.platform == "win32":
    pytest.skip( "lilybook runs in WSL on windows - run the tests inside WSL", allow_module_level = True)


def run_lilybook( book_dir, *args, timeout = 1800):
    """runs `lilybook <args>` inside book_dir and returns the CompletedProcess (stdout+stderr merged in .stdout)"""
    return subprocess.run( [ LILYBOOK] + [ str(a) for a in args],
                           cwd = str( book_dir), stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
                           text = True, errors = "replace", timeout = timeout)


def run_make( book_dir, *args, timeout = 600):
    """runs make -f lilybook.mk directly (no lilybook.log side effect) - for probing"""
    return subprocess.run( [ "make", "-f", MAKEFILE, "--no-print-directory"] + [ str(a) for a in args],
                           cwd = str( book_dir), stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
                           text = True, errors = "replace", timeout = timeout)


def pdf_pages( pdf_path):
    """list of (width, height) per page"""
    import pypdf
    reader = pypdf.PdfReader( str( pdf_path))
    return [ (float( p.mediabox.width), float( p.mediabox.height)) for p in reader.pages]


def copy_book( src_dir, dst_dir):
    """copies a book directory without git metadata and build leftovers"""
    shutil.copytree( src_dir, dst_dir,
                     ignore = shutil.ignore_patterns( ".git", "out", "__pycache__", "*.log", "_gitshort"))
    return dst_dir


def tool_available( *tools):
    return all( shutil.which( tool) for tool in tools)


def kpsewhich( *names):
    """True if kpsewhich finds all given LaTeX files"""
    if not shutil.which( "kpsewhich"):
        return False
    for name in names:
        found = subprocess.run( [ "kpsewhich", name], capture_output = True, text = True)
        if not found.stdout.strip():
            return False
    return True


TOOLCHAIN = ( "make", "lilypond", "lilypond-book", "latexmk", "pdflatex", "kpsewhich")

#: marker for tests that need the toolchain
requires_toolchain = pytest.mark.skipif( not tool_available( *TOOLCHAIN),
                                         reason = "required: " + ", ".join( TOOLCHAIN))
#: marker for booklet tests (LaTeX package pdfpages)
requires_pdfpages = pytest.mark.skipif( not kpsewhich( "pdfpages.sty"),
                                        reason = "LaTeX package pdfpages is required")


@pytest.fixture
def minimal_book( tmp_path):
    """A copy of the minimal example book in a temporary directory (returns its path)."""
    return copy_book( os.path.join( DATA_DIR, "minimal_book"), tmp_path / "minimal_book")


# ------------------------------------------------------------------------------------------------
# real books (template snapshot, liederbuch, Kommersbuch, ...)

#: environment variable with a list (os.pathsep separated) of book directories to test.
#: If unset, the template snapshot in tests/data and sibling directories of lilybook_maker are used, if existing.
BOOKS_ENV = "LILYBOOK_BOOKS"
DEFAULT_BOOK_DIRS = [
    # snapshot of https://github.com/hardmooth/lilybook_template (see README: running the tests)
    os.path.join( DATA_DIR, "template_book"),
    os.path.join( os.path.dirname( MAKER_DIR), "lilybook_template"),
    os.path.join( os.path.dirname( MAKER_DIR), "liederbuch_advent_weihnachten"),
    os.path.join( os.path.dirname( MAKER_DIR), "Kommersbuch_KSG_Chemnitz"),
]

def book_dirs():
    """returns the list of (name, path) of books to test"""
    if os.environ.get( BOOKS_ENV):
        dirs = [ d for d in os.environ[BOOKS_ENV].split( os.pathsep) if d.strip()]
    else:
        dirs = [ d for d in DEFAULT_BOOK_DIRS if os.path.isdir( d)]
    return [ (os.path.basename( os.path.normpath( d)), d) for d in dirs]


@pytest.fixture( scope = "module", params = book_dirs(), ids = lambda b: b[0])
def book( request, tmp_path_factory):
    """
    A copy of a real book in a temporary directory (module scope: the tests of a module share
    the copy). Skipped if the book, the toolchain or the book's LaTeX packages are missing.
    """
    name, src = request.param
    if not os.path.isdir( src):
        pytest.skip( "book directory '{}' not found".format( src))
    if not tool_available( *TOOLCHAIN):
        pytest.skip( "required: " + ", ".join( TOOLCHAIN))
    packages = run_make( src, "check-packages")
    if packages.returncode != 0:
        pytest.skip( "'{}': {}".format( name, packages.stdout.strip().splitlines()[0]))

    return copy_book( src, tmp_path_factory.mktemp( "book_") / name)
