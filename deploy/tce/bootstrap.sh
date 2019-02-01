#!/usr/bin/env bash

set -x
umask 022
cd ../..
export ENV=online
eval $(python deploy/env.py)
python3 bootstrap.py
