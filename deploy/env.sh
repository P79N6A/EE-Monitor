#!/usr/bin/env sh


eval $(python deploy/env.py)
export ENV=test
python3 bootstrap.py


