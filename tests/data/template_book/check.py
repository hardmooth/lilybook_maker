# -*- coding: utf-8 -*-
"""
Book specific checks. lilybook_maker (create_pdf.py) imports this file, if present, and runs Check()
before building the book.

@copyright:   Hartmut Leister, 2020, all rights reserved
@author: Hartmut Leister <hartmut.leister@gmail.com>
"""

# -- python standard imports ---
import glob
import logging
import os
import re

# -- pip ---

# -- local imports ---

#: score files that are allowed to contain \paper / \layout blocks
LAYOUT_FILES = ["default.ly", "LY-include.ly"]

def Check():
    all_ok = True

    fn_valid_pat = re.compile( r"[a-zA-Z0-9_\-\.]+\.ly", re.I)
    scores_paths = glob.glob( "scores/*.ly")
    errors = {
        "File name validation": [],
        "No page and layout in LY files": [],
    }
    for score_path in scores_paths:
        fn = os.path.basename( score_path)

        # verify scores names (no spaces)
        fn_valid = fn_valid_pat.fullmatch( fn)
        if not fn_valid:
            logging.error("File name validation failed on %s", score_path)
            errors["File name validation"].append( fn)
            all_ok = False

        with open( score_path, encoding = "utf-8") as fh:
            content = fh.read()

        if fn not in LAYOUT_FILES:
            # verify no page/layout in scores, only in default.ly
            page_matches = re.search( r"\\paper", content)
            if page_matches:
                logging.error("Detected '\\paper' in %s - page layout belongs to scores/default.ly", score_path)
                errors["No page and layout in LY files"].append( fn)
                all_ok = False

    for error_title, error_files in errors.items():
        logging.info("%s: %s", error_title, ",".join(error_files) if error_files else "all OK")

    return all_ok

if __name__ == "__main__":
    logging.basicConfig( level = logging.INFO, format = "[%(levelname)s] %(message)s")
    Check()
