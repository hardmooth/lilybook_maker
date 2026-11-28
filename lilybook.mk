# lilybook.mk - builds a songbook PDF from Lilypond scores and a LaTeX (.lytex) main file
#
# This file is shared by all books and lives in the lilybook_maker checkout. Books contain no
# build logic; run the `lilybook` wrapper (or `make -f /path/to/lilybook.mk`) inside a book directory:
#
#   lilybook            same as `lilybook pdf`
#   lilybook pdf        build <book>.pdf (incremental)
#   lilybook booklet    additionally build <book>-booklet.pdf (2 pages per sheet in booklet order)
#   lilybook scores     build a PDF for every single score in the include directories
#   lilybook check      check tools, LaTeX packages, file encodings and run the book's check.py
#   lilybook full       clean + pdf
#   lilybook clean      remove the out/ directory and generated PDFs
#
# Conventions (all auto-detected, override with VAR=value or in an optional ./book.mk):
#   LYTEX     the single *.lytex file in the book directory
#   BOOK      its base name (output: $(BOOK).pdf)
#   INCLUDES  every top level directory containing .ly or .tex files (e.g. inc scores texts)
#   OUT       directory for lilypond-book snippets and LaTeX intermediates (default: out)
#   STRICT=1  fail on LaTeX errors (default: keep going and report them, like `latexmk -f`)
#
# Requirements: GNU make, bash, lilypond, lilypond-book, latexmk, pdflatex (TeX Live or MiKTeX),
#               LaTeX package pdfpages for booklets, python3 for a book's check.py.
#               On Windows run it inside WSL.

THIS_MAKEFILE := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKER_DIR     := $(patsubst %/,%,$(dir $(THIS_MAKEFILE)))

SHELL := bash
.DEFAULT_GOAL := pdf
MAKEFLAGS += --no-builtin-rules --no-builtin-variables
.SUFFIXES:
.DELETE_ON_ERROR:

# optional per-book settings
-include book.mk

# ------------------------------------------------------------------------------------------------
# book layout

OUT   ?= out
LYTEX ?= $(wildcard *.lytex)
BOOK  ?= $(basename $(firstword $(LYTEX)))

ifneq ($(words $(LYTEX)),1)
ifeq ($(filter help clean,$(MAKECMDGOALS)),)
$(error expected exactly one .lytex file in $(CURDIR), found: $(if $(LYTEX),$(LYTEX),none). Pass LYTEX=<file> or set it in book.mk)
endif
endif

# include directories: every top level directory with .ly or .tex files (but not the output directory)
# make splits its lists at spaces, so files and directories with a space in their name are left out
# everywhere below. `find` replaces $(wildcard ...), which would return such a name as two words.
find_files    = $(shell find $(1) -maxdepth 1 \( $(2) \) ! -path '* *' 2>/dev/null | LC_ALL=C sort)
INCLUDES     ?= $(filter-out $(OUT),$(sort $(shell find . -mindepth 2 -maxdepth 2 \( -name '*.ly' -o -name '*.tex' \) ! -path '* *' 2>/dev/null | cut -d/ -f2)))
INCLUDE_DIRS := $(INCLUDES) .
ABS_INCLUDES := $(abspath $(INCLUDE_DIRS))

empty :=
space := $(empty) $(empty)
# trailing separator keeps the default search path of the TeX distribution
TEXINPUTS := $(subst $(space),:,$(ABS_INCLUDES)):

TEX_SOURCES := $(LYTEX) $(foreach d,$(INCLUDE_DIRS),$(call find_files,$(d),-name '*.tex'))
LY_ALL      := $(foreach d,$(INCLUDE_DIRS),$(call find_files,$(d),-name '*.ly'))
SOURCES     := $(TEX_SOURCES) $(LY_ALL)

# A source file with a space in its name still builds if the book uses it, but make does not see it:
# a change to it triggers no rebuild, and `scores` builds no PDF for it.
SPACED := $(shell find $(INCLUDE_DIRS) -maxdepth 1 \( -name '*.ly' -o -name '*.tex' \) -name '* *' 2>/dev/null | sed 's|^\./||;s/.*/"&"/')
ifneq ($(SPACED),)
$(warning ignoring files with a space in their name: $(SPACED))
endif

# graphics that the LaTeX sources may include. PDFs of single scores (written by `lilybook scores` or an
# editor like Frescobaldi) are left out: the book does not include them, and as prerequisites they would
# be rebuilt before every book build.
GRAPHICS    := $(filter-out $(LY_ALL:.ly=.pdf),$(foreach d,$(INCLUDES),$(call find_files,$(d),-name '*.pdf' -o -name '*.png' -o -name '*.jpg' -o -name '*.eps')))

# scores referenced by \lilypondfile{...} in the main file ...
SCORE_FILES := $(shell sed -n 's/.*\\lilypondfile\(\[[^]]*\]\)\?{\([^}]*\)}.*/\2/p' $(LYTEX) 2>/dev/null)
# ... every other .ly file is an include file (default.ly, LY-include.ly, ...). lilypond-book caches
# snippets by their text only and does not notice changes in included files, so those invalidate the cache.
LY_INCLUDED := $(filter-out $(foreach f,$(SCORE_FILES),%/$(f) $(f)),$(LY_ALL))
# single scores worth building on their own: referenced scores and other .ly files not starting with "_"
LY_SCORES   := $(filter-out $(LY_INCLUDED) $(foreach d,$(INCLUDE_DIRS),$(d)/_%),$(LY_ALL))

# ------------------------------------------------------------------------------------------------
# tools

LILYPOND      ?= lilypond
LILYPOND_BOOK ?= lilypond-book
LATEXMK       ?= latexmk
PDFLATEX      ?= pdflatex
PYTHON        ?= python3
LILYPOND_BOOK_FLAGS ?=
LATEXMK_FLAGS       ?= -pdf -silent $(if $(STRICT),-halt-on-error,-f)
BOOKLET_PAPER       ?= a4paper

# ------------------------------------------------------------------------------------------------
# targets

.PHONY: pdf booklet scores check check-tools check-packages check-encoding check-book gitshort full clean help

pdf: $(BOOK).pdf                     ## build $(BOOK).pdf (default)

booklet: $(BOOK)-booklet.pdf         ## build $(BOOK)-booklet.pdf: 2 pages per sheet in booklet order (print duplex, flip on short edge)

scores: $(LY_SCORES:.ly=.pdf)        ## build a PDF next to every single score

full:                                ## clean and rebuild everything
	$(MAKE) -f $(THIS_MAKEFILE) --no-print-directory clean
	$(MAKE) -f $(THIS_MAKEFILE) --no-print-directory pdf

clean:                               ## remove $(OUT)/ and the generated PDFs
	rm -rf $(OUT) $(if $(BOOK),$(BOOK).pdf $(BOOK)-booklet.pdf) $(LY_SCORES:.ly=.pdf)

help:                                ## show this help
	@sed -n 's/^\([a-z-]*\):.*## \(.*\)/  \1\t\2/p' $(THIS_MAKEFILE) | expand -t 12
	@echo
	@echo "book: $(BOOK)   lytex: $(LYTEX)   includes: $(INCLUDE_DIRS)   out: $(OUT)"

$(OUT):
	mkdir -p $(OUT)

# --- checks -------------------------------------------------------------------------------------
check: check-tools check-packages check-encoding check-book   ## check tools, LaTeX packages, encodings, check.py

check-tools:
	@fail=0; for t in $(LILYPOND) $(LILYPOND_BOOK) $(LATEXMK) $(PDFLATEX) kpsewhich; do \
	    if command -v $$t >/dev/null; then echo "OK       $$t -> $$(command -v $$t)"; else echo "MISSING  $$t" >&2; fail=1; fi; done; \
	  test $$fail = 0
	@echo "         $$($(LILYPOND) --version | head -1)"
	@echo "         $$($(PDFLATEX) --version | head -1)"

# packages/classes used by the sources (comments and the xetex branch of \ifxetex ... \else are ignored)
check-packages:
	@pkgs=$$(sed 's/%.*//' $(TEX_SOURCES) | awk '/\\ifxetex/{skip=1} /\\else/{skip=0} !skip' \
	        | sed -n 's/.*\\\(usepackage\|documentclass\)\(\[[^]]*\]\)\?{\([^}]*\)}.*/\3/p' | tr ',' '\n' | sed 's/^ *//;s/ *$$//' | sort -u); \
	  missing=""; for p in $$pkgs; do [ -n "$$(kpsewhich $$p.sty $$p.cls 2>/dev/null)" ] || missing="$$missing $$p"; done; \
	  if [ -n "$$missing" ]; then echo "MISSING  LaTeX packages/classes:$$missing" >&2; exit 1; fi; \
	  echo "OK       LaTeX packages: $$(echo $$pkgs | wc -w) used, all found"

# lilypond-book crashes on sources that are not UTF-8
check-encoding:
	@bad=$$(LC_ALL=C.UTF-8 grep -laxv '.*' $(SOURCES) 2>/dev/null); \
	  if [ -n "$$bad" ]; then echo "NOT UTF-8 (convert with: iconv -f latin1 -t utf-8 <file>):" >&2; echo "$$bad" | sed 's/^/         /' >&2; exit 1; fi; \
	  echo "OK       encoding: $(words $(SOURCES)) source files are UTF-8"

# book specific checks
check-book:
	@if [ -f check.py ]; then echo "==       check.py"; $(PYTHON) check.py; fi

# books may print their git commit (\input{_gitshort} in inc/intro.tex) - only written if the sources use it
gitshort:
	@if grep -q '_gitshort' $(TEX_SOURCES) 2>/dev/null; then \
	    (git rev-parse --short HEAD 2>/dev/null || echo unknown) > _gitshort; echo "==       _gitshort: $$(cat _gitshort)"; fi

# --- lilypond-book ------------------------------------------------------------------------------
$(OUT)/.ly-includes.stamp: $(LY_INCLUDED) | $(OUT)
	@if ls $(OUT)/[0-9a-f][0-9a-f] >/dev/null 2>&1; then echo "==       included .ly files changed - discarding cached snippets"; rm -rf $(OUT)/[0-9a-f][0-9a-f]; fi
	@touch $@

# lilypond-book runs LaTeX on the preamble to detect the text width. It searches only the directory
# of the .lytex file, so a preamble \input from an include directory needs TEXINPUTS. That LaTeX run
# writes into the current directory and removes only its .aux and .log, hence its own output directory.
$(OUT)/$(BOOK).tex: $(SOURCES) $(OUT)/.ly-includes.stamp | check-encoding check-book gitshort
	@echo "==       lilypond-book $(LYTEX)"
	@rm -rf $(OUT)/textwidth && mkdir $(OUT)/textwidth
	TEXINPUTS="$(TEXINPUTS)" $(LILYPOND_BOOK) --pdf --latex-program='$(PDFLATEX) -draftmode -output-directory="$(abspath $(OUT))/textwidth"' $(addprefix --include=,$(ABS_INCLUDES)) --output=$(OUT) $(LILYPOND_BOOK_FLAGS) $(LYTEX)
	@rm -rf $(OUT)/textwidth
	@test -f $@ || { echo "lilypond-book did not write $@" >&2; exit 1; }
	@touch $@

# --- LaTeX --------------------------------------------------------------------------------------
$(OUT)/$(BOOK).pdf: $(OUT)/$(BOOK).tex $(GRAPHICS)
	@echo "==       latexmk $(BOOK).tex"
	@cd $(OUT) && TEXINPUTS="$(TEXINPUTS)" $(LATEXMK) $(LATEXMK_FLAGS) $(BOOK).tex; rc=$$?; \
	  if grep -q '^!' $(BOOK).log; then echo "==       LaTeX errors ($(OUT)/$(BOOK).log):"; grep -A2 '^!' $(BOOK).log | head -40; fi; \
	  if [ $$rc != 0 ]; then $(if $(STRICT),exit $$rc,test -f $(BOOK).pdf && echo "==       PDF written despite errors (STRICT=1 fails instead)" || exit $$rc); fi
	@touch $@

$(BOOK).pdf: $(OUT)/$(BOOK).pdf
	@cp $< $@
	@echo "==       written $@ ($$(du -h $@ | cut -f1)$$(command -v pdfinfo >/dev/null && pdfinfo $@ | awk '/^Pages:/{print ", " $$2 " pages"}'))"

# --- booklet (pdfpages) -------------------------------------------------------------------------
$(OUT)/$(BOOK)-booklet.tex: $(BOOK).pdf | $(OUT)
	@printf '%s\n' '\documentclass[$(BOOKLET_PAPER),landscape]{article}' '\usepackage{pdfpages}' '\pagestyle{empty}' '\begin{document}' \
	               '\includepdf[pages=-,booklet]{$(abspath $(BOOK).pdf)}' '\end{document}' > $@

$(BOOK)-booklet.pdf: $(OUT)/$(BOOK)-booklet.tex
	@echo "==       pdflatex $(BOOK)-booklet.tex"
	@cd $(OUT) && $(PDFLATEX) -interaction=nonstopmode -halt-on-error $(BOOK)-booklet.tex >/dev/null || { grep -A2 '^!' $(BOOK)-booklet.log; exit 1; }
	@cp $(OUT)/$(BOOK)-booklet.pdf $@
	@echo "==       written $@"

# --- single scores ------------------------------------------------------------------------------
%.pdf: %.ly $(LY_INCLUDED)
	@echo "==       lilypond $<"
	@cd $(dir $<) && $(LILYPOND) -dno-point-and-click --loglevel=WARNING -o $(notdir $*) $(notdir $<)
