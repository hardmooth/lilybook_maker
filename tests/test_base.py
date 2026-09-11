# -*- coding: utf-8 -*-
"""
unit tests for base.py
"""
import configparser
import os
import sys
import time

import pytest

import base
from base import SplitCmd, PrependToPath, NormalizeOutput, RunCMD, IS_WINDOWS

windows_only = pytest.mark.skipif( not IS_WINDOWS, reason = "windows command line syntax")
posix_only   = pytest.mark.skipif( IS_WINDOWS, reason = "posix command line syntax")


# ------------------------------------------------------------------------------------------------
# SplitCmd

def test_split_cmd_splits_at_whitespace():
    assert SplitCmd( "texify --pdf --batch") == [ "texify", "--pdf", "--batch"]


@windows_only
def test_split_cmd_keeps_backslashes_and_strips_quotes_on_windows():
    cmd = r'"c:\Program Files\LilyPond\usr\bin\python.exe" lilypond-book.py'
    assert SplitCmd( cmd) == [ r"c:\Program Files\LilyPond\usr\bin\python.exe", "lilypond-book.py"]


@posix_only
def test_split_cmd_keeps_quoted_path_with_spaces_together_on_posix():
    assert SplitCmd( '"/opt/lily pond/bin/lilypond-book" --pdf') == [ "/opt/lily pond/bin/lilypond-book", "--pdf"]


# ------------------------------------------------------------------------------------------------
# PrependToPath

def test_prepend_to_path_puts_dir_first_using_platform_separator():
    env = { "PATH": "/usr/bin"}

    PrependToPath( "/opt/lilypond/bin", env = env)

    assert env["PATH"] == os.pathsep.join( [ "/opt/lilypond/bin", "/usr/bin"])


def test_prepend_to_path_ignores_empty_dirs():
    env = { "PATH": "/usr/bin"}

    PrependToPath( "", None, env = env)

    assert env["PATH"] == "/usr/bin"


def test_prepend_to_path_creates_missing_path_variable():
    env = {}

    PrependToPath( "/opt/x", env = env)

    assert env["PATH"].split( os.pathsep)[0] == "/opt/x"


# ------------------------------------------------------------------------------------------------
# NormalizeOutput

def test_normalize_output_decodes_bytes_and_collapses_linebreaks():
    assert NormalizeOutput( b"a\r\n\r\nb\r\n") == "a\nb"


def test_normalize_output_strips_trailing_whitespace():
    assert NormalizeOutput( "x\n\n\ny  \n") == "x\ny"


def test_normalize_output_truncates_long_output_to_head_and_tail():
    ten_lines = "\n".join( str(i) for i in range( 10))

    assert NormalizeOutput( ten_lines, truncate = True) == "0\n1\n... (6 lines)\n8\n9"


def test_normalize_output_does_not_truncate_short_output():
    assert NormalizeOutput( "a\nb\nc", truncate = True) == "a\nb\nc"


# ------------------------------------------------------------------------------------------------
# RunCMD

def _python( code, *argv):
    return [ sys.executable, "-c", code] + list( argv)


def test_run_cmd_returns_stdout_and_stderr():
    out, err = RunCMD( _python( "import sys; print('hello'); sys.stderr.write('warn')"), write_to_log = False)

    assert (out, err) == ("hello", "warn")


def test_run_cmd_accepts_command_line_string():
    out, _ = RunCMD( '"{0}" -c "print(1 + 1)"'.format( sys.executable), write_to_log = False)

    assert out == "2"


def test_run_cmd_passes_argument_with_spaces_unchanged():
    out, _ = RunCMD( _python( "import sys; print(sys.argv[1])", "hello world"), write_to_log = False)

    assert out == "hello world"


def test_run_cmd_raises_on_failure_with_stderr():
    with pytest.raises( RuntimeError, match = "CMD failed.*boom"):
        RunCMD( _python( "import sys; sys.stderr.write('boom'); sys.exit(3)"), write_to_log = False)


def test_run_cmd_returns_stderr_instead_of_raising_when_disabled():
    _, err = RunCMD( _python( "import sys; sys.stderr.write('boom'); sys.exit(3)"),
                     write_to_log = False, raise_on_error = False)

    assert err == "boom"


def test_run_cmd_path_pre_is_first_in_child_path():
    out, _ = RunCMD( _python( "import os; print(os.environ['PATH'].split(os.pathsep)[0])"),
                     path_pre = "/some/lilypond/bin", write_to_log = False)

    assert out == "/some/lilypond/bin"


def test_run_cmd_path_pre_does_not_modify_own_environment():
    RunCMD( _python( "pass"), path_pre = "/some/lilypond/bin", write_to_log = False)

    assert not os.environ["PATH"].startswith( "/some/lilypond/bin")


def test_run_cmd_timeout_kills_hanging_process():
    started = time.monotonic()

    RunCMD( _python( "import time; time.sleep(30)"), write_to_log = False, raise_on_error = False, timeout_sec = 1)

    assert time.monotonic() - started < 15


# ------------------------------------------------------------------------------------------------
# GetConfig

@pytest.fixture
def config_file( tmp_path, monkeypatch):
    """GetConfig() reads from a temporary config.ini and forgets the cached config afterwards"""
    path = tmp_path / "config.ini"
    monkeypatch.setattr( base, "_CONFIG_FILE", str( path))
    monkeypatch.setattr( base, "_CONFIG", None)
    return path


def test_get_config_without_file_uses_defaults( config_file):
    config = base.GetConfig()

    assert config["latex"]["CMD_PDFLATEX"] == "pdflatex"
    assert "PATH_LILYPOND" in config["lilypond"]


def test_get_config_reads_values_from_file( config_file):
    config_file.write_text( "[lilypond]\nPATH_LILYPOND = /opt/lily/bin\n[latex]\nCMD_PDFLATEX = latexmk -pdf\n")

    config = base.GetConfig()

    assert config["lilypond"]["PATH_LILYPOND"] == "/opt/lily/bin"
    assert config["latex"]["CMD_PDFLATEX"] == "latexmk -pdf"


def test_get_config_fills_keys_missing_in_file_with_defaults( config_file):
    config_file.write_text( "[lilypond]\nPATH_LILYPOND = /opt/lily/bin\n")

    config = base.GetConfig()

    assert config["latex"]["CMD_PDFLATEX"] == "pdflatex"
    assert config["lilypond"]["PATH_LILYPOND"] == "/opt/lily/bin"
