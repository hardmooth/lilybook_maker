# -*- coding: utf-8 -*-
"""
unit tests for base.py
"""
import os
import sys

import pytest

import base
from base import SplitCmd, PrependToPath, NormalizeOutput, RunCMD, IS_WINDOWS


def test_is_windows_matches_platform():
    assert IS_WINDOWS == (os.name == "nt")


def test_split_cmd_simple():
    assert SplitCmd( "pdflatex") == [ "pdflatex"]
    assert SplitCmd( "texify --pdf --batch") == [ "texify", "--pdf", "--batch"]


def test_split_cmd_quoted_path_with_spaces():
    if IS_WINDOWS:
        assert SplitCmd( r'"c:\Program Files\LilyPond\usr\bin\python.exe" lilypond-book.py') == [
            r"c:\Program Files\LilyPond\usr\bin\python.exe", "lilypond-book.py"]
    else:
        assert SplitCmd( '"/opt/lily pond/bin/lilypond-book" --pdf') == [ "/opt/lily pond/bin/lilypond-book", "--pdf"]


def test_prepend_to_path_uses_platform_separator():
    env = { "PATH": "/usr/bin"}
    PrependToPath( "/opt/lilypond/bin", env = env)
    assert env["PATH"] == os.pathsep.join( [ "/opt/lilypond/bin", "/usr/bin"])


def test_prepend_to_path_ignores_empty_dirs():
    env = { "PATH": "/usr/bin"}
    PrependToPath( "", None, env = env)
    assert env["PATH"] == "/usr/bin"


def test_prepend_to_path_without_existing_path():
    env = {}
    PrependToPath( "/opt/x", env = env)
    assert env["PATH"].split( os.pathsep)[0] == "/opt/x"


def test_normalize_output_bytes_and_linebreaks():
    assert NormalizeOutput( b"a\r\n\r\nb\r\n") == "a\nb"
    assert NormalizeOutput( "x\n\n\ny  \n") == "x\ny"


def test_normalize_output_truncate():
    long = "\n".join( str(i) for i in range( 10))
    assert NormalizeOutput( long, truncate = True) == "0\n1\n... (6 lines)\n8\n9"
    # short output is not truncated
    assert NormalizeOutput( "a\nb\nc", truncate = True) == "a\nb\nc"


def test_run_cmd_list():
    out, err = RunCMD( [ sys.executable, "-c", "import sys; print('hello'); sys.stderr.write('warn')"], write_to_log = False)
    assert out == "hello"
    assert err == "warn"


def test_run_cmd_string_with_arguments():
    cmd = '"{0}" -c "print(1 + 1)"'.format( sys.executable)
    out, _ = RunCMD( cmd, write_to_log = False)
    assert out == "2"


def test_run_cmd_argument_with_spaces_survives():
    out, _ = RunCMD( [ sys.executable, "-c", "import sys; print(sys.argv[1])", "hello world"], write_to_log = False)
    assert out == "hello world"


def test_run_cmd_raises_on_error():
    with pytest.raises( RuntimeError, match = "CMD failed"):
        RunCMD( [ sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"], write_to_log = False)


def test_run_cmd_no_raise_when_disabled():
    out, err = RunCMD( [ sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"],
                       write_to_log = False, raise_on_error = False)
    assert err == "boom"


def test_run_cmd_path_pre_is_visible_to_child():
    out, _ = RunCMD( [ sys.executable, "-c", "import os; print(os.environ['PATH'].split(os.pathsep)[0])"],
                     path_pre = "/some/lilypond/bin", write_to_log = False)
    assert out == "/some/lilypond/bin"
    # os.environ itself is not modified
    assert not os.environ["PATH"].startswith( "/some/lilypond/bin")


def test_run_cmd_timeout_kills_process():
    out, _ = RunCMD( [ sys.executable, "-c", "import time; time.sleep(30)"],
                     write_to_log = False, raise_on_error = False, timeout_sec = 1)
    assert out == ""


def test_config_defaults_have_required_keys():
    config = base.GetConfig()
    assert "PATH_LILYPOND" in config["lilypond"]
    assert "CMD_PDFLATEX" in config["latex"]
    if not IS_WINDOWS:
        assert "c:\\" not in config["lilypond"]["PATH_LILYPOND"]
