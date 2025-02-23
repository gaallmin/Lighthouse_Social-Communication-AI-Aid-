#!/bin/sh

set -xe

pip install -r requirements.txt

# Install whisper through their git, since issues occur through pip install openai-whisper
pip install git+https://github.com/openai/whisper.git

flask --app main run --debug
