#!/bin/sh

# Conversion taken from this: https://stackoverflow.com/questions/3255674/convert-audio-files-to-mp3-using-ffmpeg

# -i input 
# -vn disable video 
# -ar set audio sampling
# -ac set number of audio channels
# -b:a 192k bitrate
#
ffmpeg -i $1.mkv -vn -ar 44100 -ac 2 -b:a 192k $1.mp3
