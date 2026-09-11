# -*- coding: utf-8 -*-
"""
Dieses Skript erstellt eine Liedbuch-PDF aus Lilypond und LaTeX.

usage::
    0. clone this repository (e.g. as submodule of your boook)
    1. run from windows CMD / linux shell:
        python lilybook_maker/create_pdf.py
    2. (Windows/MikTeX) during run accept MikTeX-updates/installers

alternative usage::
    0. clone ...
    1. add lilybook_maker to PATH
    2. run lilybook.cmd (Windows) or lilybook.sh (Linux) with commands for create_pdf.py

@todo: run from external directory, e.g. d:/work/lilybook_maker/ and list logging info correctly
@todo: let setup.py crate "build.cmd"

@note: if lilypond fails with "Pango-ERROR **: Unable to open font file ...",
    one workaround could be to set the followiging environment variable::
        set FC_DEBUG=8191

@attention: doesn't work from within LiClipse/Eclipse, since lilypond-book is executes via python 2.4 (this here is python 3.*).
            But you can use VS Code or run from CMD::
                python create_pdf.py

@requires: python 3.6 or higher

@author: Hartmut Leister <Hartmut.Leister@gmail.com>
@copyright: Copyright (c) 2018 Hartmut Leister
"""

# -- python standard --
import codecs
import glob
import importlib.metadata
import locale
import logging
import os
import pprint
import re
import shutil
import subprocess
import sys
import traceback

from collections import defaultdict
from optparse import OptionParser

# -- pip --

# -- local imports --
try:
    import pdf_transform
except ModuleNotFoundError:
    pdf_transform = None
from base import RunCMD, SplitCmd, PrependToPath, IS_WINDOWS, EXIT_OK, EXIT_BAD_PARAMETERS, EXIT_BAD_PREREQUISITES, EXIT_CRITICAL, GetConfig, LogTail

# ------------------------------------------------------------------------------------------------

#: directory containing the lilypond binaries ("" means: use whatever is found in PATH)
PATH_LILYPOND = GetConfig()["lilypond"]["PATH_LILYPOND"].strip()

def _FindLilypondBook():
    """
    find a valid lilypond-book script file
    (upto version lilypond 20.* it was "lilypond-book.py", somewhen after only "lilypond-book")
    """
    candidates = []
    if PATH_LILYPOND:
        candidates += [ os.path.join( PATH_LILYPOND, "lilypond-book.py"),
                        os.path.join( PATH_LILYPOND, "lilypond-book")]
    found_in_path = shutil.which( "lilypond-book")
    if found_in_path:
        candidates.append( found_in_path)

    return next( (p for p in candidates if os.path.exists(p)), None)

PATH_LILYPOND_BOOK = _FindLilypondBook()

def _BuildLilypondBookCmd():
    """
    Lilypond-book is a python script. On Windows (older lilypond bundles) it has to be run with the
    python interpreter shipped with lilypond. On Linux (and newer bundles) it is directly executable.
    """
    if PATH_LILYPOND_BOOK is None:
        return [ "lilypond-book"]   # let the prerequisites check report a helpful error

    if IS_WINDOWS:
        lily_python = os.path.join( PATH_LILYPOND, "python.exe")
        if os.path.exists( lily_python):
            return [ lily_python, PATH_LILYPOND_BOOK]

    return [ PATH_LILYPOND_BOOK]

#: lilypond-book command (as list of arguments)
CMD_LILYPOND  = _BuildLilypondBookCmd()
#: pdflatex command (string as configured, e.g. "pdflatex" or "texify --pdf --batch")
CMD_PDFLATEX  = GetConfig()["latex"]["CMD_PDFLATEX"]
#: True, if CMD_PDFLATEX is a wrapper that takes care of multiple LaTeX runs and index creation itself
PDFLATEX_IS_WRAPPER = any( tool in CMD_PDFLATEX for tool in ("texify", "latexmk"))

#: other log files to watch for errors (MiKTeX on Windows)
OTHER_LOG_FILES = []
if os.environ.get("LOCALAPPDATA"):
    OTHER_LOG_FILES = glob.glob( os.path.join( os.environ["LOCALAPPDATA"], "MiKTeX", "*", "miktex", "log", "*.log"))

#: log file to write to (create_pdf.log in the current working directory)
LOG_FILE = os.path.join( os.getcwd(), os.path.splitext( os.path.basename( __file__))[0] + ".log")
_logger = logging.getLogger()
def loggingSetup( log_file, print_to_stdout = True):
    # reset log file if already existed
    if os.path.exists(log_file):
        os.remove(log_file)

    formatter = logging.Formatter( '%(asctime)s [%(levelname)s] %(message)s')
    _logger.setLevel( logging.DEBUG)

    # log to file
    file_handler = logging.FileHandler( filename= log_file, encoding = "utf-8")
    file_handler.setLevel( logging.DEBUG)
    file_handler.setFormatter( formatter)
    _logger.addHandler( file_handler)

    #
    if print_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel( logging.INFO)
        stdout_handler.setFormatter( formatter)
        _logger.addHandler( stdout_handler)

def sizeof_fmt(num, suffix='B'):
    """
    @see: https://stackoverflow.com/a/1094933/1498405
    """
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def _AddLilypondToPath():
    PrependToPath( PATH_LILYPOND)

PREREQUISITES = [
    { "cmd": CMD_LILYPOND + [ "--help", "-v"],
      "path_pre": PATH_LILYPOND,
      "help": "Install lilypond"},
    { "cmd": SplitCmd( CMD_PDFLATEX) + [ "--help"],
      "help": "Install PDFLaTeX (Windows: MiKTeX; Linux: texlive)", },
    { "cmd": [ "lilypond", "--help"],
      "path_pre": PATH_LILYPOND,
      "help": "add '{0}' to PATH".format( PATH_LILYPOND) if PATH_LILYPOND else "Install lilypond and make sure it is in PATH"},
]
VERSION_COMMANDS = [
    [ "lilypond", "--version"],
    [ "pdflatex", "--version"],
]
PKG_REQ_FILE = os.path.join( os.path.dirname( os.path.abspath( __file__)), "requirements_py.txt")

def _CheckPyRequirement( req):
    """Checks a single pip requirement line (e.g. "pypdf" or "pypdf>=3.0"). Returns an error message or None."""
    m = re.match( r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(.*?)\s*$", req)
    if not m:
        return "Cannot parse requirement '{}'".format( req)
    name, specifier = m.groups()

    try:
        version = importlib.metadata.version( name)
    except importlib.metadata.PackageNotFoundError:
        return "The '{}' distribution was not found and is required (try: python -m pip install -r {})".format( req, PKG_REQ_FILE)

    if specifier:
        try:
            from packaging.requirements import Requirement
            if version not in Requirement( req).specifier:
                return "{} {} is installed but {} is required".format( name, version, req)
        except ImportError:
            logging.debug("'packaging' not available - cannot verify version constraint '%s' (installed: %s)", req, version)

    return None

def _CheckPrerequisites():
    logging.info("Checking prerequisites")
    logging.debug("Running python: %s", sys.version)
    any_failed = False
    for cmd_dict in PREREQUISITES:
        ##logging.debug(">> {0}".format(pprint.pformat(cmd_dict)))
        kwargs = dict( cmd_dict)
        cmd   = kwargs.pop( "cmd")
        _help = kwargs.pop("help", None)
        cmd_str = subprocess.list2cmdline( cmd)
        try:
            stdout, stderr = RunCMD(cmd = cmd, raise_on_error = False, write_to_log = False, **kwargs)    #: pylint: disable repeated-keyword
            if stdout and not stderr:
                logging.info("<< OK: {}".format( cmd_str))
            else:
                logging.info("<< FAILED: {0}\n{1}".format( cmd_str, stderr))
                if _help:
                    logging.info("HELP: {0}".format(_help))
                any_failed = True
        except BaseException as exc:
            logging.error("<< FAILED with exception '{0}'\n{1}".format( exc, traceback.format_exc()))
            if _help:
                logging.info("HELP: {0}".format(_help))
            any_failed = True

    with open( PKG_REQ_FILE, "r", encoding = "utf8") as fh:
        requirements = list(filter( None, [ line.strip() for line in fh.readlines() if not line.startswith("#") ]))
    # check one by one to get all missing single packages
    for req in requirements:
        logging.info("Checking pip requirement '%s'", req)
        error = _CheckPyRequirement( req)
        if error:
            logging.error("<< Python Package error: %s", error)
            any_failed = True

    if any_failed:
        sys.exit(EXIT_BAD_PREREQUISITES)

    for ver_cmd in VERSION_COMMANDS:
        out, _ = RunCMD( ver_cmd, write_to_log = False)
        logging.info( "Using %s", out.splitlines()[0].strip())

def CheckEncoding( dir_path, filepatterns = r".*\.tex|.*\.lytex|.*\.ly", encoding = "utf-8"):
    r"""Checks all files in the given directory whether they are correctly encoded.
    Will log a warning for each invalidly encoded file.

    Args:
        dir_path (str): Path to directory
        filepatterns (regexp, optional): regular repression to match files. Defaults to r".*\.tex|.*\.lytex|.*\.ly".
        encoding (str, optional): Expected encoding. Defaults to "utf-8".

    Returns:
        bool: True, if all files seem valid; False if any yielded errors.
    """
    file_names = [ fname for fname in os.listdir( dir_path) if re.match( filepatterns, fname)]
    encoding_valid = True
    for fname in file_names:
        fpath = os.path.join( dir_path, fname)
        try:
            with codecs.open( fpath, "r", encoding) as fh:
                fh.read()
        except Exception as exc:
            logging.warning( "Invalidly encoded file '%s' (not %s): %s", fpath, encoding, exc)
            encoding_valid = False

    if not encoding_valid:
        logging.warning("Convert files to %s (e.g. with NotePad++ -> Encoding -> Convert to %s, or on linux: iconv -f latin1 -t utf-8)", encoding, encoding)

    return encoding_valid

INCLUDE_DEFAULTS = ["inc", "scores", os.getcwd()]
def ParseOptions( options = None, args = None, **kwargs):
    parser = OptionParser()
    parser.add_option("-L", "--lytex",      dest="lytex_file",     help="Input file name")
    parser.add_option("-I", "--include",    dest="include_dirs",   default=[],
                      help="List (comma separated) of include directories. Defaults '{0}' if existing.".format(",".join(INCLUDE_DEFAULTS)))
    parser.add_option("-o", "--out",        dest="output_dir", help="output directory for temporary files", default="out")

    parser.add_option("-F", "--full", dest="FullBuild", action="store_true", help="Do a full (re)build and discard anything in the <out> directory before building.")
    parser.add_option("-b", "--booklet", dest="Booklet", action="store_true", default=False, help="Add Booklet print output")

    parser.add_option("-s", "--strict", dest="Strict", action="store_true", default=False, help="Abort on the first error (or keep going?).")
    parser.add_option("-c", "--check", dest="Check", action="store_true", default=False, help="Only Check prerequisites and exit")

    ##################################################################################
    # adapt set parameters according to passed arguments, e.g. when used as a module #
    ##################################################################################

    if options is None:
        options, args =  parser.parse_args(sys.argv)
    elif isinstance(options, str):
        options, args =  parser.parse_args([options, args])
    elif isinstance(options, dict):
        _opts = options
        options, args =  parser.parse_args([u''])
        options.__dict__.update(_opts)
    elif isinstance(options, tuple):
        options, args = options

    options.__dict__.update(kwargs)

    ###################################
    # check some options for validity #
    ###################################

    if not options.lytex_file and not options.Check:
        arg_lytex_files = [ arg for arg in sys.argv if arg.lower().endswith("lytex") and os.path.exists( arg)]
        if len( arg_lytex_files) == 1:
            options.lytex_file = arg_lytex_files[0]
        elif len( arg_lytex_files) > 1:
            logging.error("Too many LYTEX files specified - exiting.")
            parser.print_help()
            sys.exit( EXIT_BAD_PARAMETERS)
        else:
            lytex_files = glob.glob( "*.lytex")
            if len(lytex_files) == 1:
                options.lytex_file = lytex_files[0]
                logging.info("No input file specified. Detected '{0}'.".format( options.lytex_file))
            else:
                logging.error("no input file specified. Exiting.")
                parser.print_help()
                sys.exit( EXIT_BAD_PARAMETERS)

    if isinstance(options.include_dirs, str):
        # transform given include directories to list
        options.include_dirs = options.include_dirs.split(",")
        if "." not in options.include_dirs:
            options.include_dirs.append(".")

    if not options.include_dirs:
        options.include_dirs = [inc for inc in INCLUDE_DEFAULTS if os.path.exists(inc)]

    if options.Booklet:
        if pdf_transform is None:
            logging.error("pdf_transform is not importable")

    # transform relative paths to absolute - we'll have to jump around a bit.
    options.include_dirs = [ p if os.path.isabs( p) else os.path.abspath( p) for p in options.include_dirs]

    logging.debug("Using include directories:\n%s", "\n".join( options.include_dirs))

    # check encoding of files in include directories.
    # Any included file not correctly encoded in UTF8 will most likely break lilypond down.
    # So it's better to check this now, so authors have a pointer what broke where.
    encoding_valid = all( [ CheckEncoding( inc_dir) for inc_dir in options.include_dirs])
    if not encoding_valid:
        logging.error("Invalidly encoded files found - lilypond-book will most likely fail. Convert them to UTF-8 first.")
        if options.Strict:
            sys.exit( EXIT_BAD_PREREQUISITES)

    if os.path.exists( os.path.join( "check.py")):
        sys.path.append( os.getcwd())
        try:
            import check
            if hasattr( check, "Check"):
                logging.info("Found check.py - executing book specific checks")
                check.Check()
        except Exception as exc:
            logging.error("Found check.py, but not importable: %s", exc)

    try:
        main_file, _ = os.path.splitext( options.lytex_file)
        options.tex_file = main_file + ".tex"
        options.pdf_file = main_file + ".pdf"
    except TypeError:
        options.tex_file = None
        options.pdf_file = None

    options.wdir = os.getcwd()

    return options, args

def Ly2Tex(options,args):
    PrependToPath( os.getcwd())
    cmd = CMD_LILYPOND + [ u"--pdf",
          ] + [u"--include={0}".format( inc)
               for inc in options.include_dirs
          ] + ["--output={0}".format( options.output_dir),
               options.lytex_file
               ]
    try:
        logging.info("Running lilypond-book")
        out, err = RunCMD( cmd, path_pre = PATH_LILYPOND, write_to_log = True, raise_on_error=options.Strict)
    except Exception as exc:
        logging.critical(exc)
        logging.critical(pprint.pformat(exc))
        logging.critical(traceback.format_exc())
        raise
    _tex_file = os.path.join( options.output_dir, options.tex_file)
    assert os.path.exists( _tex_file), "TeX-File '{0}' not generated.".format( _tex_file)

    with open(_tex_file, encoding = "utf-8", errors = "replace") as fh:
        line_count = len(fh.readlines())

    logging.info( "Written %s lines to %s", line_count, _tex_file)

LATEX_RERUN_PATTERN = re.compile( r"Rerun to get|Rerun LaTeX|There were undefined references|Label\(s\) may have changed")
LATEX_MAX_RUNS = 4
def _RunLatexLinux( options):
    """
    Runs pdflatex (TeX Live) the way MiKTeX's texify would do it:
      * include directories are passed via the TEXINPUTS environment variable
        (TeX Live has no --include-directory option and silently ignores it)
      * repeated runs until table of contents / references are stable
      * makeindex, if an index file was generated
    """
    env = dict( os.environ)
    # trailing separator keeps the default search paths of the TeX distribution
    env["TEXINPUTS"] = os.pathsep.join( options.include_dirs + [ env.get("TEXINPUTS", "")])

    base_name = os.path.splitext( options.tex_file)[0]
    latex_cmd = SplitCmd( CMD_PDFLATEX) + [ "-interaction=nonstopmode"]
    if options.Strict:
        latex_cmd += [ "-halt-on-error"]
    latex_cmd += [ options.tex_file]

    for run in range( 1, LATEX_MAX_RUNS + 1):
        logging.info("LaTeX run %s/%s", run, LATEX_MAX_RUNS)
        stdout, _ = RunCMD( latex_cmd, env = env, write_to_log = True, raise_on_error = False, timeout_sec = 15 * 60)

        latex_errors = [ line for line in stdout.splitlines() if line.startswith("!")]
        if latex_errors:
            logging.error("LaTeX reported %s error(s):\n%s", len( latex_errors), "\n".join( latex_errors[:20]))
            if options.Strict or not os.path.exists( options.pdf_file):
                raise RuntimeError("pdflatex failed (see {}.log in '{}')".format( base_name, options.output_dir))

        if PDFLATEX_IS_WRAPPER:
            break

        if run == 1 and os.path.exists( base_name + ".idx") and shutil.which( "makeindex"):
            logging.info("Creating index")
            RunCMD( [ "makeindex", base_name + ".idx"], write_to_log = True, raise_on_error = False)

        if run > 1 and not LATEX_RERUN_PATTERN.search( stdout):
            break

def Tex2PDF(options, args):
    logging.info("tex2pdf %s", options.tex_file)
    last_dir = os.getcwd()
    os.chdir( options.output_dir)

    try:
        if IS_WINDOWS:
            # run pdflatex / texify
            # (texify automaticaly creates index files and thus allows for an index)
            latex_args = [f"--include-directory={_dir}" for _dir in options.include_dirs ] + [ options.tex_file]
            cmd = SplitCmd( CMD_PDFLATEX) + latex_args
            RunCMD( cmd, write_to_log = True, raise_on_error=options.Strict, timeout_sec = 15 * 60)
        else:
            _RunLatexLinux( options)

        assert os.path.exists( options.pdf_file), "PDF-File '{0}' not generated in '{1}'.".format( options.pdf_file, options.output_dir)
        shutil.copyfile( options.pdf_file,
                         os.path.join( last_dir, options.pdf_file))
    finally:
        os.chdir( last_dir)

    _size = sizeof_fmt( os.stat( options.pdf_file).st_size)
    logging.info("-" * 40)
    logging.info("Written %s to %s", _size, options.pdf_file)

    if options.Booklet:
        logging.info("Creating booklet")
        booklet_file = os.path.splitext( options.pdf_file)[0] + "-booklet.pdf"
        pdf_transform.RunMain( input = options.pdf_file, output = booklet_file, pages=":", Booklet=True, Silent = True)
        if os.path.exists( booklet_file):
            logging.info("Written booklet file: %s", booklet_file)
        else:
            logging.error("No booklet file generated.")

ERROR_REGEX = [
    #re.compile( r"output"  , re.IGNORECASE),
    re.compile( r"warning" , re.IGNORECASE),
    re.compile( r"error"   , re.IGNORECASE),
    re.compile( r"critical", re.IGNORECASE),
]
#: absolute path to a log file (windows: c:\..., linux: /...)
LOG_FILE_PATTERN = re.compile(r"(?<![^\s'\"=(])(?:[A-Z]:[\\/]|/)[^ '\"]+\.log")
LOG_WATCHERS = []
def CheckLogForErrors( print_to_stdout = False, copy_to_wdir = True, wdir = None):
    grepped_lines = defaultdict(list)
    wdir = wdir or os.getcwd()

    # check our log file
    with open(LOG_FILE, "r", encoding = "utf-8", errors = "replace") as log_fh:
        for i, line in enumerate( log_fh, start = 1):
            if any( pat.search( line) for pat in ERROR_REGEX):
                grepped_lines[LOG_FILE].append( (i, line.rstrip()))

            if copy_to_wdir:
                m = LOG_FILE_PATTERN.search( line)
                if m:
                    fpath = m.group()
                    if os.path.isfile( fpath) and os.path.abspath( fpath) != os.path.abspath( LOG_FILE):
                        target = os.path.join( wdir, os.path.basename( fpath))
                        if os.path.abspath( fpath) == os.path.abspath( target):
                            continue
                        try:
                            shutil.copyfile( fpath, target)
                            logging.warning( "Found Error log file '%s' and copied to '%s'", fpath, target)
                        except Exception:
                            pass

    # check other log files (e.g. miktex for errors during pdflatex)
    for lwatcher in LOG_WATCHERS:
        if lwatcher.WasUpdated():
            grepped_lines[lwatcher.path_to_file] = lwatcher.ReadLinesNumbered( line_grep = r"CRIT|FATAL")

    if grepped_lines:
        for lfile, err_lines in grepped_lines.items():
            if not err_lines:
                continue
            msg = "{0} Errors/warnings from log file {1}:\n{2}".format( len( err_lines),
                                                                        lfile,
                                                                        "\n".join( "[{0:4}] {1}".format( i, line)
                                                                                for i, line in err_lines))
            logging.info("-" * 40)
            logging.info( msg)
            if print_to_stdout:
                print("-" * 60)
                print(msg)
                print("-" * 60)

def RunMain( options = None,
             args    = None,
             **kwargs):
    u"""
    """

    if args is None:
        args = []

    # fetch and set parameters #
    options, args = ParseOptions(options, args, **kwargs)

    if options.Check:
        _CheckPrerequisites()
        sys.exit( EXIT_OK)

    ####################
    # work starts here #
    ####################
    if options.FullBuild:
        logging.info("Full Rebuild ... deleting everything in '%s'", options.output_dir)
        if os.path.exists( options.output_dir):
            files_or_dirs = glob.glob( os.path.join( options.output_dir, "*"))
            for fd in files_or_dirs:
                if os.path.isdir( fd):
                    shutil.rmtree( fd, ignore_errors=True)
                elif os.path.isfile( fd):
                    os.remove( fd)
            logging.info("Deleted %s files/directories", len( files_or_dirs))

    if OTHER_LOG_FILES:
        for lfile in OTHER_LOG_FILES:
            LOG_WATCHERS.append( LogTail( lfile))
            logging.debug("Watching %s", lfile)

    try:
        Ly2Tex (options, args)
        Tex2PDF(options, args)
    finally:
         CheckLogForErrors( wdir = options.wdir)
    logging.info("=" * 40)

if __name__ == '__main__':
    if False:
        input("Connect to debugger?")
    loggingSetup( LOG_FILE)
    logging.info("== lilybook PDF builder ==")
    logging.info("=" * 40)
    logging.info("Working in %s", os.getcwd())
    try:
        _AddLilypondToPath()
        _CheckPrerequisites()
        RunMain()
    except Exception as exc:
        logging.exception( "UNCAUGHT EXCEPTION")
        traceback.print_exc()
        sys.exit(EXIT_CRITICAL)
