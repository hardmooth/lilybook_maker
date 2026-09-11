\include "deutsch.ly"
\version "2.18.0"

\include "default.ly"

\header {
  title = "My Sample Song"
  poet = "Text: Hartmut Leister"
  composer = "Musik: Hartmut Leister"
  tagline = ""
}

globals = {
  \time 4/4
  \key d \major
  \autoBeamOff
}

Akkorde = \chords {
  \semiGermanChords
  \set chordChanges = ##t
  % this is my
  g2 e:m | a2 d |
  % watch it
  g2 a2 | d1 |
}

StropheEins = \lyricmode { \set stanza = #"1. "
  This is my sam -- ple song.
  Watch it un -- fold
}

Melodie = \relative c'' { \globals
  h2 a4 g | a8( h) a( g) fis2 |
  g2 e4 fis | d1
  \bar "||"
}

\score {<<
    \new ChordNames { \Akkorde }
    \new Voice = "melodie" {\Melodie}
    \new Lyrics \lyricsto "melodie" {\StropheEins}
  >>
  %\midi{}
}

\markup { " " }
\markup {
  \hspace #0.1
    \line {
      \bold "2."
      \column {
        "Copy this template and"
        "get started yourself!"
      }
    }
  \hspace #0.1
}
