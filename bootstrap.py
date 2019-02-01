# coding: utf-8

import time
import schedule
import logging.config
from config import config
from es import esmetrics
from rd import rdmetrics
from cassandra import cassandramonitor
import threading

logging.config.dictConfig(config.get_log_config())


def run_threaded(func):
    worker = threading.Thread(target=func)
    worker.start()


def monitor(filename=None,cls=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            cluster_config = func(*args)
            cluster_monitor = cls(cluster_config, *args)
            schedule.every(30).seconds.do(run_threaded, cluster_monitor.monitor)
        return wrapper(filename)

    return decorator


INFRA_ES_CONFIG = ""
LARK_ES_CONFIG = ""
LARK_PASSPORT_REDIS = ""
LARK_CASSANDRA = ""
PEOPLE_WORKFLOW_REDIS = ""
MUBU_ES_CONFIG = ""
INFA_GERRIT_ES = ""


@monitor(filename=INFRA_ES_CONFIG, cls=esmetrics.EsMonitor)
def infra_es_monitor(filename):
    cluster_config = config.get_es_config(filename)
    return cluster_config


@monitor(filename=LARK_ES_CONFIG, cls=esmetrics.EsMonitor)
def lark_es_monitor(filename):
    cluster_config = config.get_es_config(filename)
    return cluster_config


@monitor(filename=MUBU_ES_CONFIG, cls=esmetrics.EsMonitor)
def mubu_es_monitor(filename):
    cluster_config = config.get_es_config(filename)
    return cluster_config


@monitor(filename=INFA_GERRIT_ES, cls=esmetrics.EsMonitor)
def infra_gerrit_es_monitor(filename):
    cluster_config = config.get_es_config(filename)
    return cluster_config


@monitor(filename=LARK_PASSPORT_REDIS, cls=rdmetrics.RedisMonitor)
def lark_passport_redis_monitor(filename):
    cluster_config = config.get_redis_config(filename)
    return cluster_config


@monitor(filename=PEOPLE_WORKFLOW_REDIS, cls=rdmetrics.RedisMonitor)
def people_workflow_redis_monitor(filename):
    cluster_config = config.get_redis_config(filename)
    return cluster_config


@monitor(filename=LARK_CASSANDRA, cls=cassandramonitor.CassandraMonitor)
def lark_cassandra_monitor(filename):
    cluster_config = config.get_cassandra_config(filename)
    return cluster_config


if __name__ == "__main__":

    while True:
        schedule.run_pending()
        time.sleep(1)
