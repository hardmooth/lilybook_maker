% Lilypond include file
% Diese Datei wird in alle anderen Lieddateien eingebunden und bestimmt
% damit das allgemeine Notenlayout.
% (This file is included by every score and defines the common score layout.)
%
% Gleichzeitig sollten damit alle \layout- und \paper-Blöcke aus dem Quellkode der Lieder entfernt werden,
% es sei denn, das Lied erfordert es.
%
% um diese Datei im Lilypond-Quellkode einzubinden, wird folgende Zeile benötigt:
%   \include "default.ly"

#(set-global-staff-size 15.0)                             % Zeilengröße, damit auch Notengröße (A5)
%#(set-global-staff-size 20.0)                            % für A4-Druck

\paper {
    % keep that in sync with inc/tex-preambel.tex -> \geometry
    #(set-paper-size "a5")
    left-margin = 1.0\cm
    right-margin = 1.0\cm
    % uncomment to show spacing
    %annotate-spacing = ##t
}

\layout {
    indent = #0                                   % kein Einzug zu Beginn
    ragged-last = ##f                             % letzte Zeile auch strecken
    \context {
        \Lyrics
            \override LyricSpace.minimum-distance = #1.8
    }
    \context {
        \Score
        \remove "Bar_number_engraver"             % keine Taktzahlen anzeigen
    }
}

% macro to add a line break within a bar (without a visible bar line)
breakInvRep = {
    \once \override Staff.BarLine.break-visibility = ##(#f #t #t)
    \break
    \bar "|:"
}
