#!/bin/zsh

cd "$(dirname "$0")" || exit 1
source .venv/bin/activate

(sleep 2; open "http://127.0.0.1:5001") &

python app.py