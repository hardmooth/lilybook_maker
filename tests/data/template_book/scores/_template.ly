% Vorlage für ein neues Lied - kopieren nach scores/<lied_name>.ly (Dateiname ohne Leerzeichen)
% (template for a new song - copy to scores/<song_name>.ly, file names without spaces)
\include "deutsch.ly"
\version "2.18.0"

\include "default.ly"

\header{
  title = "Titel des Liedes"
  poet = "Text: ..."
  composer = "Musik: ..."
  tagline = ""
}

globals = {
  \key c \major
  \time 4/4
  \autoBeamOff
}

Akkorde = \chords {
  \semiGermanChords
  \set chordChanges = ##t

}

StropheEins = \lyricmode { \set stanza = #"1. "
}

Melodie = \relative c'' { \globals

}

\score {<<
    \new ChordNames { \Akkorde }
    \new Voice = "melodie" {\Melodie}
    \new Lyrics \lyricsto "melodie" {\StropheEins}
  >>
  %\midi{}
}

% weitere Strophen als Text (further stanzas as text)
\markup { " " }
\markup {
  \hspace #0.1
    \line {
      \bold "2."
      \column {
        ""
      }
    }
    \hspace #0.2
    \line {
      \bold "3."
      \column {
        ""
      }
    }
  \hspace #0.1
}
