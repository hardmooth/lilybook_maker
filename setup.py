# -*- coding: utf-8 -*-
"""
to run a check of the local installation::
    python setup.py --check

@copyright:   Hartmut Leister, 2020, all rights reserved
@author: Hartmut Leister <hartmut.leister@gmail.com>
"""

# -- python standard imports ---
import logging
import os
import sys
from optparse import OptionParser

# -- pip ---

# -- local imports ---
from base import RunCMD, GetConfig, SaveConfig
from create_pdf import _CheckPrerequisites, _AddLilypondToPath, loggingSetup

LOG_FILE = "setup.log"

LILYPOND_PATHS = [
    r"c:\Program Files (x86)\LilyPond\usr\bin",
    r"c:\Program Files\LilyPond\usr\bin",
    r"d:\Program Files (x86)\LilyPond\usr\bin",
    r"d:\Program Files\LilyPond\usr\bin",
]
def FindLilypond( interactive = True):
    lily_paths = []
    for p in LILYPOND_PATHS:
        lily_exe = os.path.join( p, "lilypond.exe")
        if not os.path.exists( lily_exe):
            continue

        try:
            vers, _ = RunCMD( [lily_exe, "--version"], raise_on_error = False, write_to_log = False)
            vers = vers.split("\n",1)[0].strip()
            lily_paths.append( {
                "exe_path": lily_exe,
                "bin_path": p,
                "version": vers,
            })
        except Exception as exc:
            # this exe doesn't work, just skip it
            pass
    
    lily = None

    if len(lily_paths) == 1:
        [lily] = lily_paths
        logging.info( "Detected Lilypond with version=%s at %s", lily["version"], lily["exe_path"])
    
    if len(lily_paths) > 1:
        # multiple found, let the user decide
        print("Detected multiple lilypond candidates:")
        for idx, _lily in enumerate( lily_paths, start = 1):
            print( f"  [{idx}] {_lily['exe_path']} at version {_lily['version']}")
        
        while True:
            selected = input("Select lilypond: ")
            try:
                _idx = int( selected) - 1
                lily = lily_paths[_idx]
                #print(lily)
                break
            except (ValueError, IndexError):
                print("Very funny, try again!")


    if lily is None:
        logging.warning("No lilypond found.")
        return None
    
    return lily["bin_path"]

def InstallPyRequirements():
    raise NotImplementedError

def ParseOptions( options = None, args = None, **kwargs):
    parser = OptionParser()
    parser.add_option("--check", dest="CheckPrerequisites", action = "store_true", default = None,  help="Only check prerequisites")
    parser.add_option("--init",  dest="InitConfig", action="store_true", default = None, help = "Initialize setup/configuration")
    ##parser.add_option("--install", dest="InstallPyRequirements", action="store_true", default=False, help="Install all Python PIP requirements (if missing)")

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

    return options, args

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
    if options.InitConfig:
        lily_path = FindLilypond( interactive = True)

        config = GetConfig()
        config["lilypond"]["PATH_LILYPOND"] = lily_path
        config["latex"]["CMD_PDFLATEX"] = "texify --pdf --batch"

    ##if options.InstallPyRequirements:
    ##    InstallPyRequirements()

    if options.CheckPrerequisites or options.InitConfig:
        _AddLilypondToPath()
        _CheckPrerequisites()
    
    if options.InitConfig:
        SaveConfig()

if __name__ == "__main__":
    loggingSetup( LOG_FILE, print_to_stdout = True)
    RunMain()
