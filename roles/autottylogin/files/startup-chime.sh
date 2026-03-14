#!/bin/bash
# Set volume before chiming
pactl set-sink-volume @DEFAULT_SINK@ 145%

# Ascending three-note chime (C5 - E5 - G5) played via PipeWire
for freq_dur in "523.25 0.35" "659.25 0.35" "783.99 0.55"; do
    freq="${freq_dur% *}"
    dur="${freq_dur#* }"
    sox -n -r 44100 -c 2 -t wav - \
        synth "$dur" sine "$freq" \
        fade 0 "$dur" 0.2 \
        vol 0.5 | pw-play -
done
