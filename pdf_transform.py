# -*- coding: utf-8 -*-
"""
Dieses Skript transformiert PDFs
    - konkateniert freie Seitenauswahl
    - kann Seiten "2 auf 1" schreiben
    - kann Seiten als Booklet (Broschüre) anordnen

usage::
    python pdf_transform.py --input liederbuch.pdf --output liederbuch-booklet.pdf --booklet --format A4

@author: Hartmut Leister <Hartmut.Leister@gmail.com>
@copyright: Copyright (c) 2018 Hartmut Leister
"""
# ---------------------------
# python standard imports
import sys

# ---------------------------
# pip imports
try:
    import pypdf                    # pip install pypdf
except ModuleNotFoundError:
    import PyPDF2 as pypdf          # PyPDF2 >= 3.0 offers the same API as pypdf

SCALE_SPACE_UNIT_TO_CM = 2.54 / 72
SCALE_CM_TO_SPACE_UNIT = 72 / 2.54
PAGE_FORMATS = dict(
    A3 = (29.7 * SCALE_CM_TO_SPACE_UNIT, 42.0 * SCALE_CM_TO_SPACE_UNIT),
    A4 = (21.0 * SCALE_CM_TO_SPACE_UNIT, 29.7 * SCALE_CM_TO_SPACE_UNIT),
    A5 = (14.8 * SCALE_CM_TO_SPACE_UNIT, 21.0 * SCALE_CM_TO_SPACE_UNIT),
)

PAGES_ALL = ":"
def ParseOptions( options = None, args = None, **kwargs):
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-i", "--input",      dest="input",     help="Input  file name")
    parser.add_option("-o", "--output",     dest="output",    help="output file name")
    parser.add_option("-p", "--pages",      dest="pages",     default = PAGES_ALL,
                      help=("read those pages. Starts at 0. a comma-separated list of index descriptions."
                            "e.g. '0,1' (page 0, then 1) OR ':' (all pages) OR ':,:' (all pages twice)"))
    parser.add_option("-2", "--2on1",       dest="TwoOnOne",  action="store_true", default=False, help="Write as '2 on 1' (two pages side by side on a sheet twice as wide, e.g. A5 -> A4 landscape)")
    parser.add_option("-R", "--rotate",     dest="Rotate",    action="store", type="int", default=0, help="Rotate (ccw) by .. degrees.")
    parser.add_option("-b", "--booklet",    dest="Booklet",   action="store_true", default = False, help="Print as (2on1) booklet.")

    parser.add_option("-s", "--silent",     dest="Silent", action="store_true", default=False, help="No output to stdout")
    parser.add_option("-F", "--format",     dest="PageFormat", action="store", default=None, help="Target sheet format, pages are scaled to fit (any of: {})".format( ",".join( sorted(PAGE_FORMATS.keys()))))

    ##################################################################################
    # adapt set parameters according to passed arguments, e.g. when used as a module #
    ##################################################################################

    if options is None and not kwargs:
        options, args =  parser.parse_args(sys.argv)
    elif isinstance(options, str):
        options, args =  parser.parse_args([options, args])
    elif isinstance(options, dict):
        _opts = options
        options, args =  parser.parse_args([u''])
        options.__dict__.update(_opts)
    elif kwargs:
        options, args =  parser.parse_args([u''])
        options.__dict__.update( kwargs)
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

def _PageSize( page_object):
    """returns (width, height) of the given page"""
    _bbox   = page_object.mediabox
    return float(_bbox.width), float(_bbox.height)

def BookletOrder( pages):
    """
    Reorders the given page list for booklet printing (2 on 1, duplex, fold in the middle).
    Missing pages (to fill up to a multiple of 4) are added as None.

    >>> BookletOrder( [0, 1, 2, 3, 4, 5, 6, 7])
    [7, 0, 1, 6, 5, 2, 3, 4]
    >>> BookletOrder( [0, 1, 2, 3, 4, 5])
    [None, 0, 1, None, 5, 2, 3, 4]
    """
    pages = list( pages) + [None] * (-len(pages) % 4)
    ct = len( pages)
    ordered = []
    for idx in range( ct // 2):
        left, right = pages[-idx - 1], pages[idx]
        ordered += [left, right] if idx % 2 == 0 else [right, left]
    return ordered

def RunMain( options = None,
             args    = None,
             **kwargs):
    u"""
    Reads the input PDF, selects/reorders/merges pages and writes the output PDF.
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

        pdf_reader = pypdf.PdfReader(pdf_in)
        pdf_writer = pypdf.PdfWriter()
        num_pages  = len( pdf_reader.pages)

        def get_page( idx):
            """returns the page with the given index or a blank page (same size as the first page) for None"""
            if idx is None:
                w, h = _PageSize( pdf_reader.pages[0])
                return pypdf.PageObject.create_blank_page( width = w, height = h)
            return pdf_reader.pages[idx]

        if options.pages:
            if isinstance( options.pages, (list,tuple)):
                _pages = list( options.pages)
            elif isinstance( options.pages, int):
                _pages = [options.pages]
            else:
                _pages = []
                for pg_slicer in options.pages.split(","):
                    _pages += eval("list(range({ct}))[{pg}]".format( ct = num_pages,
                                                                     pg = pg_slicer))
            log("[CFG] Reading pages: {}".format( str(_pages)[1:-1]))

            if options.Booklet:
                _pages = BookletOrder( _pages)
                log("[CFG] Booklet order: {}".format( str(_pages)[1:-1]))

            if options.TwoOnOne:
                if len(_pages) % 2:
                    _pages.append( None)
                page_iter = iter( _pages)
                for idx_lt, idx_rg in zip( page_iter, page_iter):
                    log( "[MRG] Merging pages:", idx_lt, idx_rg, "->", len( pdf_writer.pages))

                    page_lt = get_page( idx_lt)
                    page_rt = get_page( idx_rg)

                    # sheet geometry: two source pages side by side.
                    #   default:  sheet is twice as wide as a source page, pages keep their size (A5 book -> A4 landscape sheets)
                    #   --format: sheet is the given format in landscape, pages are scaled to fit (and centered)
                    _width, _height = _PageSize( page_lt)
                    if options.PageFormat:
                        _sheet_h, _sheet_w = PAGE_FORMATS[ options.PageFormat]   # landscape
                        _scale = min( _sheet_w / (2 * _width), _sheet_h / _height)
                    else:
                        _sheet_w, _sheet_h = 2 * _width, _height
                        _scale = 1.0
                    _tx = (_sheet_w - 2 * _width * _scale) / 2
                    _ty = (_sheet_h - _height * _scale) / 2

                    page_merged = pypdf.PageObject.create_blank_page( width  = _sheet_w,
                                                                      height = _sheet_h)

                    page_merged.merge_transformed_page( page_lt, pypdf.Transformation().scale( _scale, _scale).translate( tx = _tx, ty = _ty))
                    page_merged.merge_transformed_page( page_rt, pypdf.Transformation().scale( _scale, _scale).translate( tx = _tx + _scale * _width, ty = _ty))

                    if options.Rotate:
                        # get same orientation as before?
                        log( "[ROT] Rotating by {} degrees counter clockwise".format( options.Rotate))
                        page_merged.rotate( -options.Rotate)

                    pdf_writer.add_page( page_merged)
            else:
                for pg in _pages:
                    pg_object = get_page( pg)

                    if options.PageFormat:
                        _width, _height = _PageSize( pg_object)
                        if _width < _height:
                            _scale = (PAGE_FORMATS[options.PageFormat][0] / _width)
                        else:
                            _scale = (PAGE_FORMATS[options.PageFormat][0] / _height)
                        pg_object.scale_by( _scale)

                    pdf_writer.add_page( pg_object)

        with open( options.output, "wb") as pdf_out:
            log( "[OUT] Writing to", options.output)
            pdf_writer.write( pdf_out)

if __name__ == "__main__":
    RunMain()
