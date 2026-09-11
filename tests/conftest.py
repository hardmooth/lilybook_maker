# -*- coding: utf-8 -*-
"""
pytest fixtures and helpers shared by all tests
"""
import os
import re
import shutil
import subprocess
import sys

import pytest

MAKER_DIR = os.path.dirname( os.path.dirname( os.path.abspath( __file__)))
DATA_DIR  = os.path.join( os.path.dirname( os.path.abspath( __file__)), "data")

# make base.py, create_pdf.py, ... importable
if MAKER_DIR not in sys.path:
    sys.path.insert( 0, MAKER_DIR)


def tool_available( *tools):
    return all( shutil.which( tool) for tool in tools)

def toolchain_available():
    """lilypond, lilypond-book and pdflatex are usable (lilypond-book is looked up the way create_pdf does it)"""
    import create_pdf
    return bool( tool_available( "lilypond", "pdflatex") and create_pdf.PATH_LILYPOND_BOOK)

#: marker for tests that need the full toolchain (lilypond-book + pdflatex)
requires_toolchain = pytest.mark.skipif(
    not toolchain_available(),
    reason = "lilypond, lilypond-book and pdflatex are required")


def run_create_pdf( book_dir, *args, timeout = 1800):
    """runs create_pdf.py inside book_dir and returns the CompletedProcess"""
    script = os.path.join( MAKER_DIR, "create_pdf.py")
    return subprocess.run( [ sys.executable, script] + list( args),
                           cwd = str( book_dir), capture_output = True, text = True, timeout = timeout)


def pdf_page_count( pdf_path):
    import pypdf
    return len( pypdf.PdfReader( str( pdf_path)).pages)


def copy_book( src_dir, dst_dir):
    """copies a book directory without git metadata and build leftovers"""
    shutil.copytree( src_dir, dst_dir,
                     ignore = shutil.ignore_patterns( ".git", "out", "__pycache__", "*.log", "_gitshort"))
    return dst_dir


# ------------------------------------------------------------------------------------------------
# real books (lilybook_template, liederbuch, ...)

#: environment variable with a list (os.pathsep separated) of book directories to test.
#: If unset, the template snapshot in tests/data and sibling directories of lilybook_maker are used, if existing.
BOOKS_ENV = "LILYBOOK_BOOKS"
DEFAULT_BOOK_DIRS = [
    # snapshot of https://github.com/hardmooth/lilybook_template (see README: running the tests)
    os.path.join( DATA_DIR, "template_book"),
    os.path.join( os.path.dirname( MAKER_DIR), "lilybook_template"),
    os.path.join( os.path.dirname( MAKER_DIR), "liederbuch_advent_weihnachten"),
]

def book_dirs():
    """returns the list of (name, path) of books to test"""
    if os.environ.get( BOOKS_ENV):
        dirs = [ d for d in os.environ[BOOKS_ENV].split( os.pathsep) if d.strip()]
    else:
        dirs = [ d for d in DEFAULT_BOOK_DIRS if os.path.isdir( d)]
    return [ (os.path.basename( os.path.normpath( d)), d) for d in dirs]


_USEPACKAGE = re.compile( r"^\s*\\(?:usepackage|documentclass)(?:\[[^\]]*\])?\{([^}]*)\}", re.M)
def missing_latex_packages( book_dir):
    """returns the LaTeX packages/classes used by the book that kpsewhich cannot find"""
    if not shutil.which( "kpsewhich"):
        return [ "kpsewhich"]

    names = set()
    for root, _dirs, files in os.walk( book_dir):
        if ".git" in root or os.path.basename( root) == "out":
            continue
        for fname in files:
            if fname.endswith( (".tex", ".lytex")):
                with open( os.path.join( root, fname), encoding = "utf-8", errors = "replace") as fh:
                    content = fh.read()
                # the xetex branch of the preamble is never used by pdflatex
                content = re.sub( r"\\ifxetex.*?\\else", "", content, flags = re.S)
                for m in _USEPACKAGE.finditer( content):
                    names.update( n.strip() for n in m.group(1).split( ",") if n.strip())

    missing = []
    for name in sorted( names):
        found = subprocess.run( [ "kpsewhich", name + ".sty", name + ".cls"], capture_output = True, text = True)
        if not found.stdout.strip():
            missing.append( name)
    return missing


@pytest.fixture( scope = "module", params = book_dirs(), ids = lambda b: b[0])
def book( request, tmp_path_factory):
    """
    A copy of a real book in a temporary directory (module scope: the tests of a module share
    the copy and thus can test incremental builds). Skipped if the book or LaTeX packages are missing.
    """
    name, src = request.param
    if not os.path.isdir( src):
        pytest.skip( "book directory '{}' not found".format( src))
    if not toolchain_available():
        pytest.skip( "lilypond, lilypond-book and pdflatex are required")
    missing = missing_latex_packages( src)
    if missing:
        pytest.skip( "LaTeX packages missing for '{}': {}".format( name, ", ".join( missing)))

    dst = tmp_path_factory.mktemp( "book_") / name
    return copy_book( src, dst)


@pytest.fixture
def minimal_book( tmp_path):
    """A copy of the minimal example book in a temporary directory (returns its path)."""
    return copy_book( os.path.join( DATA_DIR, "minimal_book"), tmp_path / "minimal_book")

