# -*- coding: utf-8 -*-
"""
Dieses Skript erstellt eine Liedbuch-PDF aus Lilypond und LaTeX.

usage::
    0. clone this repository (e.g. as submodule of your boook)
    1. run from windows CMD:
        python lilybook_maker/create_pdf.py 
    2. during run accept MikTeX-updates/installers

@attention: funktioniert nicht aus LiClipse/Eclipse heraus, da lilypond-book via python 2.4 ausgeführt wird.
            Besser aus CMD ausführen::
                python create_pdf.py

@requires: python 3.6 or higher

@author: Hartmut Leister <Hartmut.Leister@gmail.com>
@copyright: Copyright (c) 2018 Hartmut Leister
"""

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

EXIT_BAD_PARAMETERS    = 1
EXIT_BAD_PREREQUISITES = 2
EXIT_CRITICAL          = 4 

PATH_LILYPOND = r"c:\Program Files (x86)\LilyPond\usr\bin"
CMD_LILYPOND  = u'"{py}" "{lp}"'.format( py = os.path.join( PATH_LILYPOND, u"python.exe"),
                                         lp = os.path.join( PATH_LILYPOND, u"lilypond-book.py"))
CMD_PDFLATEX  = u"pdflatex"

LOG_FILE = os.path.join( os.getcwd(), os.path.basename( __file__).rstrip("pyco") + "log")
def loggingSetup():
    # create file handler which logs even debug messages
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    logging.basicConfig(
        format = '%(asctime)s [%(levelname)s] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = LOG_FILE,
        level=logging.DEBUG
    )

def RunCMD(cmd, raise_on_error = True, write_to_log = True, decode_std = True, env = None, path_pre = None):
    def _ToStr( str_or_b):
        _as_str = str_or_b.decode(locale.getpreferredencoding()) if not isinstance( str_or_b, str) else str_or_b
        _as_str = _as_str.replace("\r\n", "\n")
        return _as_str
    
    if write_to_log:
        logging.info ( "CMD: {0}".format( cmd))

    if isinstance(cmd, list):
        cmd = " ".join(cmd)
        
    if path_pre:
        _env  = env if env else os.environ
        _path = "{0}:{1}".format( path_pre if isinstance( path_pre, str) else ";".join(path_pre), os.environ["path"])
        _env["path"] = _path
        _env["PATH"] = _path
        logging.debug("ENV:{0}".format( pprint.pformat( _env)))
    else:
        _env = None
         
    try:
        p = subprocess.Popen( cmd,
                              stdout = subprocess.PIPE,
                              stderr = subprocess.PIPE,
                              env    = _env)
        stdout, stderr = p.communicate()
        ret_code = p.returncode
    except Exception as exc:
        logging.critical( "CMD FAILED with exception:")
        logging.critical( "CMD: {0}".format( cmd))
        logging.critical( "EXC: {0}".format( repr(exc)))
        logging.exception( "exception:")
        sys.exit(EXIT_CRITICAL)
    
    if write_to_log:
        logging.debug( "OUT: {0}".format( _ToStr( stdout)))
        logging.debug( "ERR: {0}".format( _ToStr( stderr)))
    
    if ret_code and stderr and raise_on_error:
        _msg = ("CMD FAILED: {0}\n"
                "-- STDOUT --\n"
                "{1}\n"
                "-- STDERR -- \n"
                "{2}\n"
                "------------"
               ).format( cmd, 
                         stdout.rstrip().decode(locale.getpreferredencoding(), errors = "replace"), 
                         stderr.rstrip().decode(locale.getpreferredencoding(), errors = "replace"))
        raise RuntimeError("CMD failed: '{0}'".format(_msg))
    
    if decode_std:
        stdout = stdout.rstrip().decode(locale.getpreferredencoding(), errors = "replace") 
        stderr = stderr.rstrip().decode(locale.getpreferredencoding(), errors = "replace")
    
    return stdout, stderr

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
import pprint
def _CheckPrerequisites():
    logging.info("Checking prerequisites")
    any_failed = False
    for cmd_dict in PREREQUISITES:
        logging.debug(">> {0}".format(pprint.pformat(cmd_dict)))
        cmd = cmd_dict.pop( "cmd")
        _help = cmd_dict.pop("help", None)
        try:
            stdout, stderr = RunCMD(cmd = cmd, raise_on_error = False, write_to_log = False, **cmd_dict)    #: pylint: disable repeated-keyword
            if stdout and not stderr:
                logging.info("<< OK")
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

INCLUDE_DEFAULTS = ["inc", "scores"]
def ParseOptions( options = None, args = None, **kwargs):
    parser = OptionParser()
    parser.add_option("-L", "--lytex",      dest="lytex_file",     help="Input file name")
    parser.add_option("-I", "--include",    dest="include_dirs",   default=[],
                      help="List (comma separated) of include directories. Defaults '{0}' if existing.".format(",".join(INCLUDE_DEFAULTS)))
    parser.add_option("-o", "--out",        dest="output_dir", help="output directory for temporary files", default="out")

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
        lytex_files = glob.glob( "*.lytex")
        if len(lytex_files) == 1:
            options.lytex_file = lytex_files[0]
            logging.info("No input file specified. Detected '{0}'.".format( options.lytex_file))
        else:
            logging.error("no input file specified. Exiting.")
            parser.print_help()
            sys.exit( EXIT_BAD_PARAMETERS)
    
    if isinstance(options.include_dirs, str):
        options.include_dirs = options.include_dirs.split(",")
    if not options.include_dirs:
        options.include_dirs = INCLUDE_DEFAULTS
    
    main_file, _ = os.path.splitext( options.lytex_file)
    options.tex_file = main_file + ".tex"
    options.pdf_file = main_file + ".pdf"

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
        out, err = RunCMD( cmd, path_pre = PATH_LILYPOND, write_to_log = True)
    except Exception as exc:
        logging.critical(exc)
        logging.critical(pprint.pformat(exc))
        logging.critical(traceback.format_exc())
        raise
    _tex_file = os.path.join( options.output_dir, options.tex_file)
    assert os.path.exists( _tex_file), "TeX-File '{0}' not generated.".format( _tex_file)

def Tex2PDF(options, args):
    last_dir = os.getcwd()
    os.chdir( options.output_dir)
    
    cmd = CMD_PDFLATEX + " --interaction=nonstopmode {0}".format(options.tex_file)
    RunCMD( cmd, write_to_log = True)
    
    shutil.copyfile( options.pdf_file,
                     os.path.join( last_dir,           options.pdf_file))
    
    os.chdir( last_dir)

ERROR_REGEX = [
    re.compile( r"output"  , re.IGNORECASE),
    re.compile( r"warning" , re.IGNORECASE),
    re.compile( r"error"   , re.IGNORECASE),
    re.compile( r"critical", re.IGNORECASE),
]
def CheckLogForErrors():
    grepped_lines = []
    with open(LOG_FILE, "r") as log_fh:
        for i, line in enumerate( log_fh):
            if any( pat.search( line) for pat in ERROR_REGEX):
                grepped_lines.append( (i, line.rstrip()))
    if grepped_lines:
        msg = "{0} Errors/warnings from log file {1}:\n{2}".format( len( grepped_lines),
                                                                    LOG_FILE,
                                                                    "\n".join( "[{0:4}] {1}".format( i, line) 
                                                                               for i, line in grepped_lines))
        logging.info( msg)
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
    Ly2Tex (options, args)
    Tex2PDF(options, args)
    CheckLogForErrors()
    
if __name__ == '__main__':
    loggingSetup()
    logging.info("Working in %s", os.getcwd())
    try:
        os.environ["path"] = "{0};{1}".format( os.environ["path"], PATH_LILYPOND)
        os.environ["PATH"] = "{0};{1}".format( os.environ["PATH"], PATH_LILYPOND)
        _CheckPrerequisites()
        RunMain()
    except Exception as exc:
        logging.exception( "UNCAUGHT EXCEPTION")
        traceback.print_exc()
        sys.exit(EXIT_CRITICAL)