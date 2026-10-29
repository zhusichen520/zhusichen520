#!/bin/sh
cd "$(dirname "$0")"
python3 launch_web.py
printf "\nPress Enter to close this window.\n"
read answer
