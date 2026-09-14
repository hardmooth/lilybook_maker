% common layout, included by every score
#(set-global-staff-size 16)
\layout {
  indent = #0
  \context {
    \Score
    \remove "Bar_number_engraver"
  }
}
