# -*- coding: utf-8 -*-
"""
auxiliary functions used in other modules/scripts
@copyright:   Hartmut Leister, 2020, all rights reserved
@author: Hartmut Leister <hartmut.leister@gmail.com>
"""

# -- python standard imports ---
import configparser
import locale
import logging
import os
import shutil
import subprocess
import sys

# -- pip ---

# -- local imports ---


# ------------------------------------------------------------------------------------------------
EXIT_BAD_PARAMETERS    = 1
EXIT_BAD_PREREQUISITES = 2
EXIT_CRITICAL          = 4 

_CONFIG = None
_CONFIG_FILE = os.path.join( os.path.dirname( os.path.abspath(__file__)), "config.ini")
_CONFIG_DEFAULT = {
    'lilypond': { 
        'PATH_LILYPOND': 'c:\\Program Files (x86)\\LilyPond\\usr\\bin',
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
                logging.warning("Supplied config section '%s' not in default config.")

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

    with open( _CONFIG_FILE, "w") as fh:
        config.write( fh)
    logging.info("Written configuration to %s", _CONFIG_FILE)


def RunCMD(cmd, raise_on_error = True, write_to_log = True, decode_std = True, env = None, path_pre = None):
    def _ToStr( str_or_b):
        _as_str = str_or_b.decode(locale.getpreferredencoding(), errors = "replace") if not isinstance( str_or_b, str) else str_or_b
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
        ##logging.debug("ENV:{0}".format( pprint.pformat( _env)))
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
