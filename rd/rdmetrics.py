# coding: utf-8

import sys
import logging

from anacapa.program import metrics

from rediscluster import StrictRedisCluster

logger = logging.getLogger()


class RedisMonitor():
    DEFAULT_INDICES = ["redis_git_dirty", "arch_bits", "uptime_in_seconds", "uptime_in_days", "hz", "lru_clock",
                       "connected_clients", "client_longest_output_list", "client_biggest_input_buf", "blocked_clients",
                       "used_memory", "used_memory_rss", "used_memory_peak", "used_memory_peak_perc",
                       "used_memory_overhead",
                       "used_memory_startup", "used_memory_dataset", "used_memory_dataset_perc", "total_system_memory",
                       "used_memory_lua", "maxmemory", "mem_fragmentation_ratio", "active_defrag_running",
                       "lazyfree_pending_objects", "loading", "rdb_changes_since_last_save", "rdb_bgsave_in_progress",
                       "rdb_last_save_time", "rdb_last_bgsave_time_sec", "rdb_current_bgsave_time_sec",
                       "rdb_last_cow_size",
                       "aof_current_size", "aof_rewrite_buffer_length", "aof_pending_bio_fsync", "aof_delayed_fsync",
                       "aof_base_size", "aof_pending_rewrite", "aof_buffer_length", "aof_enabled",
                       "aof_rewrite_in_progress",
                       "aof_rewrite_scheduled", "aof_last_rewrite_time_sec", "aof_current_rewrite_time_sec",
                       "aof_last_cow_size", "total_connections_received", "total_commands_processed",
                       "instantaneous_ops_per_sec", "total_net_input_bytes", "total_net_output_bytes",
                       "instantaneous_input_kbps", "instantaneous_output_kbps", "rejected_connections", "sync_full",
                       "sync_partial_ok", "sync_partial_err", "expired_keys", "expired_stale_perc",
                       "expired_time_cap_reached_count", "evicted_keys", "keyspace_hits", "keyspace_misses",
                       "pubsub_channels",
                       "pubsub_channels", "pubsub_patterns", "latest_fork_usec", "migrate_cached_sockets",
                       "slave_expires_tracked_keys", "active_defrag_hits", "active_defrag_misses",
                       "active_defrag_key_hits",
                       "active_defrag_key_misses", "connected_slaves", "master_repl_offset", "second_repl_offset",
                       "repl_backlog_active", "repl_backlog_size", "repl_backlog_first_byte_offset",
                       "repl_backlog_histlen",
                       "used_cpu_sys", "used_cpu_user", "used_cpu_sys_children", "used_cpu_user_children",
                       "db0.avg_ttl",
                       "db0.expires", "db0.keys"
                       ]

    # DEFAULT_INDICES = ["redis_git_dirty", "arch_bits"]

    def __init__(self, config, filename, indices=DEFAULT_INDICES):
        self.indices = indices
        self.TAGKV = {}
        self.id_indice = "redis_build_id"
        self.id = None
        self.filename = filename
        self.hosts = config["hosts"]
        self.metrics_namespace_prefix = '' + '.rd.' + self.filename
        startup_nodes = []
        for host in self.hosts:
            temp = {}
            ip = host.split(":")[0]
            port = host.split(":")[1]
            temp["host"] = ip
            temp["port"] = port
            startup_nodes.append(temp)
        try:
            self.client = StrictRedisCluster(startup_nodes=startup_nodes, password=config['password'])
            self.define_tagkv()

        except Exception as e:
            logger.info("Connect Error!",e)
            sys.exit(1)

    def monitor(self):
        metrics.define_counter("indices.monitor.error", self.metrics_namespace_prefix)
        try:
            info = self.client.info()

            for node_name in info:
                cur_tagk = {"instance": node_name.replace(".", "_").replace(":", "_")}
                logger.info("cur_tagk={}".format(cur_tagk))
                node_value = info[node_name]
                for path in self.indices:
                    indices_value = self.find(node_value, path)
                    if indices_value is None:
                        logger.info("can not find path={}".format(path))
                        continue
                    metrics.emit_store(path, indices_value, prefix=self.metrics_namespace_prefix, tagkv=cur_tagk)

                    logger.info("key={},value={},tagv={}".format(path, indices_value, cur_tagk))

        except Exception as e:
            logger.warning(e)
            metrics.emit_counter("indices.monitor.error", 1, prefix=self.metrics_namespace_prefix,
                                 tagkv={"instance": self.filename})

        finally:
            pass

    def define_tagkv(self):
        tagv_arr = [self.filename]
        for host in self.hosts:
            temp = {}
            ip = host.split(":")[0]
            port = host.split(":")[1]
            temp["host"] = ip
            temp["port"] = port
            tagv_arr.append(host.replace(".", "_").replace(":", "_"))
        metrics.define_tagkv('instance', tagv_arr)
        for index in self.indices:
            metrics.define_store(index, self.metrics_namespace_prefix)

    def find(self, temp, path):
        segments = path.split('.')
        logging.debug("segments={}".format(segments))
        for segment in segments:
            temp = temp.get(segment)
            logging.debug("segment={},temp={}".format(segment, temp))
            if temp is None:
                return None

        logging.debug("segment={}, find value={}".format(segment, temp))
        return temp
