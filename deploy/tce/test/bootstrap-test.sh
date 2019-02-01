#!/usr/bin/env bash

set -x
umask 022
cd ../../..
export ENV=test
eval $(python deploy/env.py)
exec gunicorn -c es/esmetrics.py
