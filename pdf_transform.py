# -*- coding: utf-8 -*-
"""
Dieses Skript transformiert PDFs
    - konkateniert freie Seitenauswahl
    - kann Seiten "2 auf 1" schreiben

@author: Hartmut Leister <Hartmut.Leister@gmail.com>
@copyright: Copyright (c) 2018 Hartmut Leister
"""
# ---------------------------
# python standard imports
import math
import sys

# ---------------------------
# pip imports
import PyPDF2   # pip install PyPDF2

PAGES_ALL = ":"
def ParseOptions( options = None, args = None, **kwargs):
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-i", "--input",      dest="input",     help="Input  file name")
    parser.add_option("-o", "--output",     dest="output",    help="output file name")
    parser.add_option("-p", "--pages",      dest="pages",
                      help=("read those pages. Starts at 0. a comma-separated list of index descriptions."
                            "e.g. '0,1' (page 0, then 1) OR ':' (all pages) OR ':,:' (all pages twice)"))
    parser.add_option("-2", "--2on1",       dest="TwoOnOne",  action="store_true", default="False", help="Write as '2 on 1'")
    parser.add_option("-R", "--rotate",     dest="Rotate",    action="store", type="int", default=0, help="Rotate (ccw) by .. degrees.")
    parser.add_option("-b", "--booklet",    dest="Booklet",   action="store_true", default = False, help="Print as (2on1) booklet.")
    
    parser.add_option("-s", "--silent",     dest="Silent", action="store_true", default=False, help="No output to stdout")

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

    if not options.input or not options.output:
        parser.print_help()
        sys.exit(1)
    
    if options.Booklet:
        options.TwoOnOne = True

    if options.pages != PAGES_ALL:
        try:
            options.pages = [int(pg) for pg in options.pages.split(",")]
        except (ValueError, TypeError):
            pass

    return options, args

TWO_ON_ONE_LAYOUT = "/OneColumn"
def RunMain( options = None,
             args    = None,
             **kwargs):
    u"""
    Retrieves the test overview and writes HTML (if configured)
    """
    if args is None:
        args = []

    # fetch and set parameters #
    options, args = ParseOptions(options, args, **kwargs)

    def log(*x):
        if not options.Silent:
            print(*x)

    ####################
    # work starts here #
    ####################
    log( "[IN]  Reading from", options.input)
    with open( options.input, "rb") as pdf_in:

        pdf_reader = PyPDF2.PdfFileReader(pdf_in)
        pdf_writer = PyPDF2.PdfFileWriter()

        if options.pages:
            if isinstance( options.pages, (list,tuple)):
                _pages = options.pages
            elif isinstance( options.pages, int):
                _pages = (options.pages,)
            else:
                _pages = []
                for pg_slicer in options.pages.split(","):
                    _pages += eval("list(range({ct}))[{pg}]".format( ct = pdf_reader.getNumPages(),
                                                                     pg = pg_slicer))
            log("[CFG] Reading pages: {}".format( str(_pages)[1:-1]))

            if options.Booklet:
                # ensure pages is multiple of 4:
                ct = len(_pages)
                _pages += [None] * (-ct % 4)
                # reorder to booklet ordering [ 7,0, 1,6, 5,2, 3,4 ]
                _pages = sum( [ ([ _pages[idx], _pages[-idx -1]] if idx % 2 else [ _pages[-idx -1], _pages[idx]]) for idx in range(ct//2) ], [])

            if options.TwoOnOne:
                page_iter = iter( _pages)
                for idx_lt, idx_rg in zip( page_iter, page_iter):
                    log( "[MRG] Merging pages:", idx_lt, idx_rg, "->", pdf_writer.getNumPages())

                    page_lt = pdf_reader.getPage(idx_lt)
                    page_rt = pdf_reader.getPage( idx_rg)

                    # get height and width
                    _bbox   = page_lt.mediaBox
                    _width  = float(_bbox[2] - _bbox[0])
                    _height = float(_bbox[3] - _bbox[1])
                    _scale  = math.sqrt(0.5)

                    # create empty page with swapped width/height
                    page_merged = PyPDF2.pdf.PageObject.createBlankPage( width  = _height,
                                                                         height = _width)

                    page_merged.mergeScaledPage          ( page_lt, scale = _scale)
                    page_merged.mergeScaledTranslatedPage( page_rt, scale = _scale, tx = _scale * _width, ty = 0)

                    if options.Rotate:
                        # get same orientation as before?
                        log( "[ROT] Rotating by {} degrees counter clockwise".format( options.Rotate))
                        page_merged.rotateCounterClockwise( options.Rotate)

                    pdf_writer.addPage( page_merged)
            else:
                for pg in _pages:
                    pdf_writer.addPage( pdf_reader.getPage(pg))

        with open( options.output, "wb") as pdf_out:
            log( "[OUT] Writing to", options.output)
            pdf_writer.write( pdf_out)

if __name__ == "__main__":
    if False:
        RunMain( pages    = ":,:",
                 input    = 'WiseGuys_Staendchen_Melodie.pdf',
                 output   = 'WiseGuys_Staendchen_Melodie_2on1.pdf',
                 Rotate   = 90,
                 TwoOnOne = True)
    RunMain()