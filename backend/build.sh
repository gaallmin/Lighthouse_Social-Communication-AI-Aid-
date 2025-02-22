#!/bin/sh

set -xe

pip install -r requirements.txt

flask --app main run --debug
