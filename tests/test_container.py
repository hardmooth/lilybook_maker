# -*- coding: utf-8 -*-
"""
tests for lilybook-container: the wrapper, the image built from the Containerfile and lilybook inside it

They need podman or docker on the host, but neither lilypond nor LaTeX. Select or skip them with
`pytest -m container` and `pytest -m "not container"`.
"""
import os
import shutil
import subprocess

import pytest

from conftest import pdf_pages, copy_book, DATA_DIR, MAKER_DIR

WRAPPER = os.path.join( MAKER_DIR, "lilybook-container")
BOOK    = "minimal_book"
SCORE   = os.path.join( "scores", "alle_meine_entchen")


def engine():
    """the engine the wrapper will pick, or None"""
    return os.environ.get( "LILYBOOK_ENGINE") or next( (e for e in ( "podman", "docker") if shutil.which( e)), None)


def engine_usable():
    if not engine() or not shutil.which( engine()):
        return False
    return subprocess.run( [ engine(), "info"], capture_output = True).returncode == 0


pytestmark = pytest.mark.container


def run_container( book_dir, *args, env = None, timeout = 3600):
    """runs `lilybook-container <args>` inside book_dir (stdout+stderr merged in .stdout)"""
    return subprocess.run( [ WRAPPER] + [ str(a) for a in args],
                           cwd = str( book_dir), stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
                           text = True, errors = "replace", timeout = timeout, env = env)


def assert_ok( result):
    assert result.returncode == 0, result.stdout


@pytest.fixture( scope = "session")
def image( tmp_path_factory):
    """
    Rebuilds the image once per test session. The image contains a copy of lilybook.mk, so an
    image from an earlier checkout would test outdated build logic.
    """
    if not engine_usable():
        pytest.skip( "a usable podman or docker is required")
    book = copy_book( os.path.join( DATA_DIR, BOOK), tmp_path_factory.mktemp( "image") / BOOK)
    result = run_container( book, "--rebuild", "help")
    assert_ok( result)
    return result


@pytest.fixture
def minimal_book( image, tmp_path):
    return copy_book( os.path.join( DATA_DIR, BOOK), tmp_path / BOOK)


# ------------------------------------------------------------------------------------------------
# the wrapper

def test_rebuild_builds_the_image_and_runs_the_target( image):
    assert "book: minimal_book" in image.stdout
    assert subprocess.run( [ engine(), "image", "inspect", os.environ.get( "LILYBOOK_IMAGE", "lilybook")],
                           capture_output = True).returncode == 0


def test_make_variables_reach_lilybook( minimal_book):
    result = run_container( minimal_book, "help", "OUT=other_out")

    assert_ok( result)
    assert "out: other_out" in result.stdout


def test_failing_target_gives_nonzero_exit_code( minimal_book):
    result = run_container( minimal_book, "no_such_target")

    assert result.returncode != 0
    assert "no_such_target" in result.stdout


def test_missing_engine_is_reported( tmp_path):
    # a PATH with the tools the wrapper itself needs, but without podman and docker
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ( "bash", "env", "dirname", "readlink"):
        os.symlink( shutil.which( tool), bin_dir / tool)
    env = { "PATH": str( bin_dir)}

    result = subprocess.run( [ str( bin_dir / "bash"), WRAPPER, "help"], cwd = str( tmp_path), env = env,
                             stdout = subprocess.PIPE, stderr = subprocess.STDOUT, text = True)

    assert result.returncode == 2
    assert "neither podman nor docker found" in result.stdout


# ------------------------------------------------------------------------------------------------
# the toolchain inside the image

def test_check_finds_all_tools_and_latex_packages( minimal_book):
    result = run_container( minimal_book, "check")

    assert_ok( result)
    assert "MISSING" not in result.stdout
    assert "LaTeX packages" in result.stdout


def test_check_finds_the_latex_packages_of_the_template( image, tmp_path):
    book = copy_book( os.path.join( DATA_DIR, "template_book"), tmp_path / "template_book")

    result = run_container( book, "check-packages")

    assert_ok( result)


def test_gitshort_reads_the_commit_of_the_mounted_book( minimal_book):
    # the gitshort target only writes _gitshort if a TeX source mentions it
    (minimal_book / "inc" / "uses_gitshort.tex").write_text( "% \\input{_gitshort}\n")
    git = [ "git", "-c", "user.name=test", "-c", "user.email=test@example.org"]
    for command in ( [ "init", "-q"], [ "add", "-A"], [ "commit", "-q", "-m", "book"]):
        subprocess.run( git + command, cwd = str( minimal_book), check = True)
    commit = subprocess.run( git + [ "rev-parse", "--short", "HEAD"], cwd = str( minimal_book),
                             capture_output = True, text = True, check = True).stdout.strip()

    result = run_container( minimal_book, "gitshort")

    assert_ok( result)
    assert (minimal_book / "_gitshort").read_text().strip() == commit


# ------------------------------------------------------------------------------------------------
# the book, built once and inspected by several tests

@pytest.fixture( scope = "module")
def built( image, tmp_path_factory):
    book = copy_book( os.path.join( DATA_DIR, BOOK), tmp_path_factory.mktemp( "container_built") / BOOK)
    result = run_container( book, "booklet")
    assert_ok( result)
    return book, result


def test_build_writes_pdf_into_the_book_directory( built):
    book, result = built

    assert "LaTeX errors" not in result.stdout, result.stdout
    assert len( pdf_pages( book / (BOOK + ".pdf"))) >= 4


def test_booklet_has_landscape_sheets( built):
    book, _ = built

    width, height = pdf_pages( book / (BOOK + "-booklet.pdf"))[0]
    assert width > height


def test_generated_files_belong_to_the_calling_user( built):
    book, _ = built

    for path in ( book / (BOOK + ".pdf"), book / "out", book / "lilybook.log"):
        assert os.stat( path).st_uid == os.getuid(), path


# ------------------------------------------------------------------------------------------------
# single scores

def test_single_score_is_built_without_the_book( minimal_book):
    result = run_container( minimal_book, SCORE + ".pdf")

    assert_ok( result)
    assert len( pdf_pages( minimal_book / (SCORE + ".pdf"))) == 1
    assert not (minimal_book / (BOOK + ".pdf")).exists()
    assert not (minimal_book / "out").exists()


def test_invalid_score_fails_and_leaves_no_pdf( minimal_book):
    (minimal_book / (SCORE + ".ly")).write_text( '\\version "2.24.0"\n{ c4 d e \\nosuchcommand f\n')

    result = run_container( minimal_book, SCORE + ".pdf")

    assert result.returncode != 0
    assert "alle_meine_entchen.ly:2" in result.stdout
    assert "error" in result.stdout
    assert not (minimal_book / (SCORE + ".pdf")).exists()
