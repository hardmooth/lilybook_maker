# -*- coding: utf-8 -*-
"""
auxiliary functions used in other modules/scripts
@copyright:   Hartmut Leister, 2020, all rights reserved
@author: Hartmut Leister <hartmut.leister@gmail.com>
"""

# -- python standard imports ---
import configparser
import enum
import locale
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading

# -- pip ---

# -- local imports ---


# ------------------------------------------------------------------------------------------------
EXIT_OK                = 0
EXIT_BAD_PARAMETERS    = 1
EXIT_BAD_PREREQUISITES = 2
EXIT_CRITICAL          = 4

#: True if running on Windows, False on Linux/macOS/...
IS_WINDOWS = os.name == "nt"

def FindToolDir( tool_name):
    """Returns the directory of a tool found in PATH (or "" if not found)."""
    tool_path = shutil.which( tool_name)
    return os.path.dirname( tool_path) if tool_path else ""

_CONFIG = None
_CONFIG_FILE = os.path.join( os.path.dirname( os.path.abspath(__file__)), "config.ini")
_CONFIG_DEFAULT = {
    'lilypond': {
        # directory of the lilypond binaries. Leave empty to use the lilypond found in PATH.
        'PATH_LILYPOND': 'c:\\Program Files (x86)\\LilyPond\\usr\\bin' if IS_WINDOWS else FindToolDir( "lilypond"),
    },
    'latex': {
        'CMD_PDFLATEX': 'pdflatex',
    },
}
def GetConfig():
    global _CONFIG

    if _CONFIG:
        return _CONFIG

    config = configparser.ConfigParser()
    if os.path.exists( _CONFIG_FILE):
        config.read( _CONFIG_FILE)
        # fill in any keys missing in the config file with their defaults
        for section, sdata in _CONFIG_DEFAULT.items():
            if section not in config:
                config[section] = {}
            for key, val in sdata.items():
                config[section].setdefault( key, val)
    else:
        _UpdateConfig( config, _CONFIG_DEFAULT, verify = False)

    _CONFIG = config

    return _CONFIG

def _UpdateConfig( config, data, verify = True):
    for section, sdata in data.items():
        if verify:
            if section in _CONFIG_DEFAULT:
                default_sdata = _CONFIG_DEFAULT[section]
                assert all( key in sdata for key in default_sdata)
            else:
                logging.warning("Supplied config section '%s' not in default config.", section)

        if section not in config:
            config[section] = {}
        for key, val in sdata.items():
            config[section][key] = val


def SaveConfig( verify = True, backup_if_existing = False):
    config = GetConfig()

    # verify that all (section,key) of _CONFIG_DEFAULT are present in the current config
    for section, sdata in _CONFIG_DEFAULT.items():
        assert section in config.sections()
        for key in sdata:
            assert key in config[section].keys()

    if backup_if_existing and os.path.exists( _CONFIG_FILE):
        bkp_path = _CONFIG_FILE + ".bak"
        logging.warning("Config file %s already existing. Backup to %s", _CONFIG_FILE, bkp_path)
        shutil.copyfile( _CONFIG_FILE, bkp_path)

    with open( _CONFIG_FILE, "w", encoding = "utf-8") as fh:
        config.write( fh)
    logging.info("Written configuration to %s", _CONFIG_FILE)

def PrependToPath( *dirs, env = None):
    """Prepends the given directories to the PATH of the given environment (defaults to os.environ).
    Empty directories are ignored. Returns the environment."""
    if env is None:
        env = os.environ
    dirs = [ d for d in dirs if d]
    if dirs:
        env["PATH"] = os.pathsep.join( dirs + [ env.get("PATH", "")])
    return env

def NormalizeOutput( data, truncate = False):
    if isinstance( data, bytes):
        data = data.decode(locale.getpreferredencoding(), errors = "replace")

    # remove mult-line-breaks and trailing whitespaces
    data = re.sub(r"[\r\n]+", "\n", data).rstrip()

    if truncate:
        data_lines = data.splitlines()
        if len(data_lines) > 4:
            data = "\n".join( data_lines[:2] + ["... ({} lines)".format( len(data_lines) - 4)] + data_lines[-2:])

    return data

class LogTail:
    """
    Implements a log file watcher like the bash equivalent:
        tail -f <path_to_file> | grep <line_grep>

    Usage::
        log_watcher = LogTail(path_to_file)
        # do something lengthy
        print("Log file has {}".format( "changed:" if log_watcher.WasUpdated() else "no changes"))
        if log_watcher.WasUpdated():
            print(log_watcher.Read(line_grep = ))

    """
    def __init__(self, path_to_file) -> None:
        self.path_to_file = path_to_file
        self._mod_time = os.path.getmtime( path_to_file)
        self._base_size = os.path.getsize( path_to_file)

    def WasUpdated(self):
        curr_mod_time = os.path.getmtime( self.path_to_file)
        return curr_mod_time != self._mod_time

    def Read( self, read_mode = "r", line_grep = None):
        with open( self.path_to_file, read_mode) as fh:
            fh.seek(self._base_size)

            data = fh.read()

        # return all data
        if line_grep is None:
            return data

        # only return lines that match/contain the given regex
        lines = data.splitlines()
        return "\n".join( l for l in lines if re.search( line_grep, l))

    def ReadLinesNumbered( self, line_grep):
        with open( self.path_to_file, "r") as fh:
            # read the stuff before
            data_prev = fh.read(self._base_size)
            line_offset = len(data_prev.splitlines())

            # now the actual data
            data = fh.read()

        lines_numbered = [
            (lno, line)
            for lno, line in enumerate( data.splitlines(), start = line_offset)
            if re.search( line_grep, line)
        ]

        return lines_numbered


def SplitCmd( cmd_str):
    """Splits a command line string into a list of arguments (platform aware)."""
    if IS_WINDOWS:
        # non-posix mode keeps backslashes (c:\Program Files\...) intact, but leaves quotes on the tokens
        return [ tok[1:-1] if len(tok) >= 2 and tok[0] == tok[-1] == '"' else tok
                 for tok in shlex.split( cmd_str, posix = False)]
    return shlex.split( cmd_str)

def _PrepareCmd( cmd):
    """
    Brings a command (string or list) into the form suitable for subprocess.Popen on this platform.

    * Windows: a single command line string (as CreateProcess expects it)
    * others:  a list of arguments (a string is split shell-like)

    Commands configured as strings (e.g. CMD_PDFLATEX = "texify --pdf --batch") have to be split
    with SplitCmd() before adding further arguments as list elements.
    """
    if IS_WINDOWS:
        return cmd if isinstance( cmd, str) else subprocess.list2cmdline( [ str(c) for c in cmd])

    if isinstance( cmd, str):
        return SplitCmd( cmd)
    return [ str(c) for c in cmd]

def RunCMD(cmd, raise_on_error = True, write_to_log = True, decode_std = True, env = None, path_pre = None, timeout_sec = None, cwd = None):
    cmd = _PrepareCmd( cmd)
    cmd_str = cmd if isinstance( cmd, str) else subprocess.list2cmdline( cmd)

    if write_to_log:
        logging.info ( "CMD: {0}".format( cmd_str))

    if path_pre:
        _env = dict( env if env else os.environ)
        PrependToPath( *([path_pre] if isinstance( path_pre, str) else path_pre), env = _env)
        ##logging.debug("ENV:{0}".format( pprint.pformat( _env)))
    else:
        _env = env

    timer = None

    try:
        p = subprocess.Popen( cmd,
                              stdout = subprocess.PIPE,
                              stderr = subprocess.PIPE,
                              env    = _env,
                              cwd    = cwd)
        if timeout_sec is not None:
            timer = threading.Timer( timeout_sec, p.kill)
            timer.start()
        stdout, stderr = p.communicate()
        ret_code = p.returncode
    except Exception as exc:
        logging.critical( "CMD FAILED with exception:")
        logging.critical( "CMD: {0}".format( cmd_str))
        logging.critical( "EXC: {0}".format( repr(exc)))
        logging.exception( "exception:")
        sys.exit(EXIT_CRITICAL)
    finally:
        if timer:
            timer.cancel()

    if write_to_log:
        logging.debug( "OUT: {0}".format( NormalizeOutput( stdout)))
        logging.debug( "ERR: {0}".format( NormalizeOutput( stderr)))

    if ret_code and stderr and raise_on_error:
        _msg = ("CMD FAILED (rc={3}): {0}\n"
                "-- STDOUT --\n"
                "{1}\n"
                "-- STDERR -- \n"
                "{2}\n"
                "------------"
               ).format( cmd_str,
                         NormalizeOutput(stdout, truncate = write_to_log),
                         NormalizeOutput(stderr, truncate = write_to_log),
                         ret_code)
        raise RuntimeError("CMD failed: '{0}'".format(_msg))

    if decode_std:
        stdout = NormalizeOutput(stdout)
        stderr = NormalizeOutput(stderr)

    return stdout, stderr
