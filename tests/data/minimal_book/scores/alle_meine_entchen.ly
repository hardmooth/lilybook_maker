\version "2.24.0"
\include "default.ly"
\header {
  title = "Alle meine Entchen"
  tagline = ##f
}

melody = \relative c' {
  \clef treble
  \key c \major
  \time 2/4
  c8 d e f | g2 | g2 | a8 a a a | g2 | a8 a a a | g2 | f8 f f f | e2 | e2 | d8 d d d | c2 \bar "|."
}

text = \lyricmode {
  Al -- le mei -- ne Ent -- chen schwim -- men auf dem See, schwim -- men auf dem See,
  Köpf -- chen in das Was -- ser, Schwänz -- chen in die Höh'.
}

\score {
  <<
    \new Voice = "mel" { \melody }
    \new Lyrics \lyricsto "mel" { \text }
  >>
}
