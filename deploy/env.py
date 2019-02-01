#!/usr/bin/env python3
# coding: utf-8
"""
version: 3
"""

import os.path as op

deploy_root = op.dirname(__file__)
project_root = op.abspath(op.join(deploy_root, '..'))
codebase_root = op.abspath(op.join(project_root, '..', '..'))

python_path = []

system_codebase_root = '/opt/tiger/'

for project in ('anacapa',):
    user_project_root = op.join(codebase_root, project)
    system_project_root = op.join(system_codebase_root, project)

    if op.exists(user_project_root):
        python_path.append(user_project_root)
    else:
        python_path.append(system_project_root)

python_path.append(codebase_root)
python_path.append('$PYTHONPATH')
path_s = ':'.join(python_path)

print('export PYTHONPATH={0}'.format(path_s))
print('export PROJECT_ROOT={0}'.format(project_root))
print('export CODEBASE_ROOT={0}'.format(codebase_root))
