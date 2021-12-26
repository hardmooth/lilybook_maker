# -*- coding: utf-8 -*-
"""
Dieses Skript erstellt eine Liedbuch-PDF aus Lilypond und LaTeX.

usage::
    0. clone this repository (e.g. as submodule of your boook)
    1. run from windows CMD:
        python lilybook_maker/create_pdf.py 
    2. during run accept MikTeX-updates/installers

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
import glob
import locale
import logging
import os
import re
import shutil
import subprocess
import sys
import traceback

from optparse import OptionParser

# -- pip --

# -- local imports --
from base import RunCMD, EXIT_BAD_PARAMETERS, EXIT_BAD_PREREQUISITES, EXIT_CRITICAL, GetConfig

# ------------------------------------------------------------------------------------------------

PATH_LILYPOND = GetConfig()["lilypond"]["PATH_LILYPOND"]
#: find a valid lilypond-book python script file (upto version lilypond 20.* it was "lilypond-book.py", somewhen after only "lilypond-book")
PATH_LILYPOND_BOOK = next( p for p in [os.path.join( PATH_LILYPOND, u"lilypond-book.py"), os.path.join( PATH_LILYPOND, u"lilypond-book")] if os.path.exists(p))
CMD_LILYPOND  = u'"{py}" "{lp}"'.format( py = os.path.join( PATH_LILYPOND, u"python.exe"),
                                         lp = PATH_LILYPOND_BOOK)
CMD_PDFLATEX  = GetConfig()["latex"]["CMD_PDFLATEX"]

#: log file to write to (create_pdf.log in the current working directory)
LOG_FILE = os.path.join( os.getcwd(), os.path.basename( __file__).rstrip("pyco") + "log")
_logger = logging.getLogger()
def loggingSetup( log_file, print_to_stdout = True):
    # reset log file if already existed
    if os.path.exists(log_file):
        os.remove(log_file)

    formatter = logging.Formatter( '%(asctime)s [%(levelname)s] %(message)s')
    _logger.setLevel( logging.DEBUG)

    # log to file
    file_handler = logging.FileHandler( filename= log_file)
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
    os.environ["path"] = "{0};{1}".format( os.environ["path"], PATH_LILYPOND)
    os.environ["PATH"] = "{0};{1}".format( os.environ["PATH"], PATH_LILYPOND)

PREREQUISITES = [
    { "cmd": "{0} --help -v".format( CMD_LILYPOND),
      "env": dict( os.environ, 
                   PATH = "{};{}".format( PATH_LILYPOND, os.environ["PATH"]),
                   path = "{};{}".format( PATH_LILYPOND, os.environ["path"])),
      "help": "Install lilypond"},
    { "cmd": "{0} --help".format( CMD_PDFLATEX),
      "help": "Install PDFLaTeX", },
    { "cmd": "lilypond --help",
      "help": "add '{0}' to %PATH%".format( PATH_LILYPOND)},
]
VERSION_COMMANDS = [
    "lilypond --version",
    "pdflatex --version",
]
import pprint
def _CheckPrerequisites():
    logging.info("Checking prerequisites")
    any_failed = False
    for cmd_dict in PREREQUISITES:
        ##logging.debug(">> {0}".format(pprint.pformat(cmd_dict)))
        cmd = cmd_dict.pop( "cmd")
        _help = cmd_dict.pop("help", None)
        try:
            stdout, stderr = RunCMD(cmd = cmd, raise_on_error = False, write_to_log = False, **cmd_dict)    #: pylint: disable repeated-keyword
            if stdout and not stderr:
                logging.info("<< OK: {}".format( cmd))
            else:
                logging.info("<< FAILED:\n{0}".format( stderr))
                any_failed = True
        except BaseException as exc:
            logging.error("<< FAILED with exception '{0}'\n{1}".format( exc, traceback.format_exc()))
            if _help:
                logging.info("HELP: {0}".format(_help))
            any_failed = True
    
    if any_failed:
        sys.exit(EXIT_BAD_PREREQUISITES)
    
    for ver_cmd in VERSION_COMMANDS:
        out, _ = RunCMD( ver_cmd, write_to_log = False)
        logging.info( "Using %s", out.splitlines()[0].strip())

INCLUDE_DEFAULTS = ["inc", "scores", os.getcwd()]
def ParseOptions( options = None, args = None, **kwargs):
    parser = OptionParser()
    parser.add_option("-L", "--lytex",      dest="lytex_file",     help="Input file name")
    parser.add_option("-I", "--include",    dest="include_dirs",   default=[],
                      help="List (comma separated) of include directories. Defaults '{0}' if existing.".format(",".join(INCLUDE_DEFAULTS)))
    parser.add_option("-o", "--out",        dest="output_dir", help="output directory for temporary files", default="out")

    parser.add_option("-F", "--full", dest="FullBuild", action="store_true", help="Do a full (re)build and discard anything in the <out> directory before building.")

    parser.add_option("-s", "--strict", dest="Strict", action="store_true", default=False, help="Abort on the first error (or keep going?).")

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

    if not options.lytex_file:
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
        options.include_dirs = INCLUDE_DEFAULTS
    
    # transform relative paths to absolute - we'll have to jump around a bit.
    options.include_dirs = [ p if os.path.isabs( p) else os.path.abspath( p) for p in options.include_dirs]

    logging.debug("Using include directories:\n%s", "\n".join( options.include_dirs))

    main_file, _ = os.path.splitext( options.lytex_file)
    options.tex_file = main_file + ".tex"
    options.pdf_file = main_file + ".pdf"

    options.wdir = os.getcwd()

    return options, args

def Ly2Tex(options,args):
    os.environ["path"] = "{0};{1}".format( os.environ["path"], os.getcwd())
    os.environ["PATH"] = "{0};{1}".format( os.environ["PATH"], os.getcwd())
    cmd = [ CMD_LILYPOND, u"--pdf", 
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
    
    with open(_tex_file) as fh:
        line_count = len(fh.readlines())
    
    logging.info( "Written %s lines to %s", line_count, _tex_file)

def Tex2PDF(options, args):
    logging.info("tex2pdf %s", options.tex_file)
    last_dir = os.getcwd()
    os.chdir( options.output_dir)

    latex_args = [f"--include-directory={_dir}" for _dir in options.include_dirs ] + [ options.tex_file]

    # run pdflatex / texify
    # (texify automaticaly creates index files and thus allows for an index)
    cmd = [ CMD_PDFLATEX] + latex_args
    RunCMD( cmd, write_to_log = True, raise_on_error=options.Strict, timeout_sec = 15 * 60)

    shutil.copyfile( options.pdf_file,
                     os.path.join( last_dir, options.pdf_file))
    
    os.chdir( last_dir)
    _size = sizeof_fmt( os.stat( options.pdf_file).st_size)
    logging.info("-" * 40)
    logging.info("Written %s to %s", _size, options.pdf_file)

ERROR_REGEX = [
    re.compile( r"output"  , re.IGNORECASE),
    re.compile( r"warning" , re.IGNORECASE),
    re.compile( r"error"   , re.IGNORECASE),
    re.compile( r"critical", re.IGNORECASE),
]
LOG_FILE_PATTERN = re.compile(r"[A-Z]:[\\/][^ ]+\.log")
def CheckLogForErrors( print_to_stdout = False, copy_to_wdir = True):
    grepped_lines = []
    with open(LOG_FILE, "r") as log_fh:
        for i, line in enumerate( log_fh):
            if any( pat.search( line) for pat in ERROR_REGEX):
                grepped_lines.append( (i, line.rstrip()))
            
            if copy_to_wdir:
                m = LOG_FILE_PATTERN.search( line)
                if m:
                    fpath = m.group()
                    if os.path.exists( fpath):
                        try:
                            shutil.copyfile( fpath, options.wdir)
                            logging.warning( "Found Error log file '%s' and copied to '%s'", fpath, options.wdir)
                        except:
                            pass
        
    if grepped_lines:
        msg = "{0} Errors/warnings from log file {1}:\n{2}".format( len( grepped_lines),
                                                                    LOG_FILE,
                                                                    "\n".join( "[{0:4}] {1}".format( i, line) 
                                                                               for i, line in grepped_lines))
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
    
    ####################
    # work starts here #
    ####################
    if options.FullBuild:
        logging.info("Full Rebuild ... deleting in %s", options.output_dir)
        if os.path.exists( options.output_dir):
            files_or_dirs = glob.glob( os.path.join( options.output_dir, "*"))
            for fd in files_or_dirs:
                if os.path.isdir( fd):
                    shutil.rmtree( fd, ignore_errors=True)
                elif os.path.isfile( fd):
                    os.remove( fd)
            logging.info("Deleted %s files/directories", len( files_or_dirs))

    try:
        Ly2Tex (options, args)
        Tex2PDF(options, args)
    finally:
         CheckLogForErrors()
    logging.info("=" * 40)
    
if __name__ == '__main__':
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