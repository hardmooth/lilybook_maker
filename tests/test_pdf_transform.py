# -*- coding: utf-8 -*-
"""
tests for pdf_transform.py (booklet / 2 on 1)
"""
import pytest

import pdf_transform
from pdf_transform import BookletOrder, PAGE_FORMATS

pypdf = pdf_transform.pypdf

A5 = PAGE_FORMATS["A5"]
A4 = PAGE_FORMATS["A4"]


def _make_pdf( path, num_pages, size = A5):
    """writes a PDF with num_pages blank pages of the given (width, height)"""
    writer = pypdf.PdfWriter()
    for _ in range( num_pages):
        writer.add_blank_page( width = size[0], height = size[1])
    with open( path, "wb") as fh:
        writer.write( fh)
    return path


def _sizes( path):
    reader = pypdf.PdfReader( path)
    return [ (round( float( p.mediabox.width)), round( float( p.mediabox.height))) for p in reader.pages]


def test_booklet_order_multiple_of_four():
    assert BookletOrder( range( 8)) == [ 7, 0, 1, 6, 5, 2, 3, 4]
    assert BookletOrder( range( 4)) == [ 3, 0, 1, 2]


def test_booklet_order_pads_with_none():
    assert BookletOrder( range( 6)) == [ None, 0, 1, None, 5, 2, 3, 4]
    assert BookletOrder( range( 5)) == [ None, 0, 1, None, None, 2, 3, 4]
    assert BookletOrder( []) == []


def test_booklet_order_keeps_every_page_once():
    for n in range( 1, 20):
        ordered = BookletOrder( range( n))
        assert len( ordered) % 4 == 0
        assert sorted( p for p in ordered if p is not None) == list( range( n))


def test_booklet_a5_gives_a4_landscape_sheets( tmp_path):
    src = _make_pdf( tmp_path / "book.pdf", 12)
    out = tmp_path / "booklet.pdf"
    pdf_transform.RunMain( input = str( src), output = str( out), pages = ":", Booklet = True, Silent = True)

    sizes = _sizes( out)
    assert len( sizes) == 6
    assert all( s == (round( 2 * A5[0]), round( A5[1])) for s in sizes)


def test_booklet_pads_odd_page_count( tmp_path):
    src = _make_pdf( tmp_path / "book.pdf", 7)
    out = tmp_path / "booklet.pdf"
    pdf_transform.RunMain( input = str( src), output = str( out), pages = ":", Booklet = True, Silent = True)
    # 7 pages -> padded to 8 -> 4 sheets
    assert len( _sizes( out)) == 4


def test_two_on_one_with_format_scales_to_sheet( tmp_path):
    src = _make_pdf( tmp_path / "book.pdf", 4, size = A4)
    out = tmp_path / "2on1.pdf"
    pdf_transform.RunMain( input = str( src), output = str( out), pages = ":", TwoOnOne = True, PageFormat = "A4", Silent = True)
    sizes = _sizes( out)
    assert len( sizes) == 2
    # A4 landscape sheets
    assert all( s == (round( A4[1]), round( A4[0])) for s in sizes)


def test_page_selection( tmp_path):
    src = _make_pdf( tmp_path / "book.pdf", 5)
    out = tmp_path / "sel.pdf"
    pdf_transform.RunMain( input = str( src), output = str( out), pages = "0,2,4", Silent = True)
    assert len( _sizes( out)) == 3

    out2 = tmp_path / "twice.pdf"
    pdf_transform.RunMain( input = str( src), output = str( out2), pages = ":,:", Silent = True)
    assert len( _sizes( out2)) == 10


def test_missing_arguments_exit():
    with pytest.raises( SystemExit):
        pdf_transform.RunMain( input = "x.pdf", output = None, Silent = True)
