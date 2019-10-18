#!/bin/bash

IFS='
'

voice='(<voice>.*?<\/voice>\s*)'
stem='(<stem>.*?<\/stem>\s*)'
tp='<type>.*?<\/type>'
dot='(<dot>.*?<\/dot>\s*)*'
accidental='(<accidental>.*?<\/accidental>)?'
tm='(<time-modification>.*?<\/time-modification>)?'

re="s/(^\s*)${voice}${stem}(${tp}\s*${dot}\s*${accidental}\s*${tm}\s*)/\1\2\n\1\4\3/gm"

mxl=$1
copy=$(basename $mxl)_stems.musicxml
cp $1 $copy
perl -0777pi -e $re $copy

echo corrected musicxml is in $copy
