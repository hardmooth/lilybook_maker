# -*- coding: utf-8 -*-
"""
to run a check of the local installation::
    python setup.py --check

@copyright:   Hartmut Leister, 2020, all rights reserved
@author: Hartmut Leister <hartmut.leister@gmail.com>
"""

# -- python standard imports ---
import logging
import sys
from optparse import OptionParser

# -- pip ---

# -- local imports ---
from create_pdf import _CheckPrerequisites, _AddLilypondToPath, loggingSetup

LOG_FILE = "setup.log"

def ParseOptions( options = None, args = None, **kwargs):
    parser = OptionParser()
    parser.add_option("--check", dest="CheckPrerequisites", action = "store_true", default = None,  help="Only check prerequisites")

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
    if options.CheckPrerequisites:
        _CheckPrerequisites()

if __name__ == "__main__":
    loggingSetup( LOG_FILE, print_to_stdout = True)
    _AddLilypondToPath()
    RunMain()
