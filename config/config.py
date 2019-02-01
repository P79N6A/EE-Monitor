# coding: utf-8

import os
from anacapa.conf.kms import kms_config

ENV = os.environ.get("ENV")
if not ENV:
    ENV = "test"

LOG_LEVEL = 'INFO'


def get_log_config():
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s %(levelname)s %(message)s'
            },
            'console': {
                'format': "%(asctime)s [%(thread)d] %(levelname)s %(filename)s %(lineno)s %(funcName)s\t%(message)s"
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console'
            }
        },
        'root': {
            'handlers': ['console'],
            'level': LOG_LEVEL
        }
    }


def get_es_config(filename):
    if ENV == "test":
        if filename == '':
            return {
                'hosts': [],
                'username': "",
                'password': "",
                "use_ssl": True
            }
        elif filename == '':
            return {
                'hosts': [],
                'username': "",
                'password': "",
                "use_ssl": True
            }
        elif filename == '':
            return {
                'hosts': [],
                'username': "",
                'password': "",
                "use_ssl": True
            }
        elif filename == '':
            return {
                'hosts': [],
                'username': "",
                'password': "",
                "use_ssl": True
            }
    elif ENV == "online":
        config = ClusterConfiguration()
        return config.load_elasticsearch_conf(filename)
    else:
        return {}


def get_redis_config(filename):
    if ENV == "test":
        return {
            'hosts': [],
            'password': ""
        }
    elif ENV == "online":
        config = ClusterConfiguration()
        return config.load_redis_conf(filename)
    else:
        return {}


def get_cassandra_config(filename):
    if filename == '':
        return {"hosts": []
                }
    else:
        return {}


APP_ROLE = "cluster-monitor"
SECRET = ""

es_config = {

    "": {
        "hosts": "",
        "username": "",
        "password": "",
        "use_ssl": True
    },
    "": {
        "hosts": "",
        "username": "",
        "password": "",
        "use_ssl": True
    },
    "": {
        "hosts": "",
        "username": "",
        "password": "",
        "use_ssl": True
    },
    "": {
        "hosts": "",
        "username": "",
        "password": "",
        "use_ssl": True
    }

}

redis_config = {
    '': {
        'hosts': ,
        'password':
    },
    '': {
        'hosts': ,
        'password':
    }
}


class ClusterConfiguration():
    def __init__(self, app_role=APP_ROLE, secret=SECRET):
        self.kms = kms_config(
            approle=app_role,
            secret=secret,
        )

    def load_elasticsearch_conf(self, filename):
        return {
            'hosts':
            'username':
            'password':
            'use_ssl':
        }

    def load_redis_conf(self, filename):
        return {
            'hosts':
            'password':
        }
