import logging
import json
from elasticsearch import Elasticsearch
from anacapa.program import metrics

logger = logging.getLogger()


class EsMonitor():
    DEFAULT_INDICES = ["indices.search.query_total", "indices.search.query_time_in_millis",
                       "indices.search.query_current",
                       "indices.search.fetch_total", "indices.search.fetch_time_in_millis",
                       "indices.search.fetch_current",
                       "indices.indexing.index_total", "indices.indexing.index_time_in_millis",
                       "indices.indexing.index_current", "indices.refresh.total",
                       "indices.refresh.total_time_in_millis",
                       "indices.flush.total", "indices.flush.total_time_in_millis",
                       "indices.query_cache.memory_size_in_bytes", "indices.query_cache.evictions",
                       "indices.fielddata.memory_size_in_bytes", "indices.fielddata.evictions",
                       "indices.request_cache.memory_size_in_bytes", "indices.request_cache.evictions",
                       "os.cpu.percent",
                       "os.cpu.load_average.1m", "os.cpu.load_average.5m", "os.cpu.load_average.15m",
                       "os.mem.free_percent",
                       "os.mem.used_percent", "os.mem.total_in_bytes", "os.mem.free_in_bytes", "os.mem.used_in_bytes",
                       "os.swap.total_in_bytes", "os.swap.free_in_bytes", "os.swap.used_in_bytes",
                       "process.cpu.percent",
                       "process.cpu.total_in_millis", "process.mem.total_virtual_in_bytes",
                       "process.open_file_descriptors",
                       "process.max_file_descriptors", "jvm.gc.collectors.young.collection_count",
                       "jvm.gc.collectors.young.collection_time_in_millis", "jvm.gc.collectors.old.collection_count",
                       "jvm.gc.collectors.old.collection_time_in_millis", "jvm.mem.heap_used_percent",
                       "jvm.mem.heap_used_in_bytes", "jvm.mem.heap_committed_in_bytes", "thread_pool.bulk.queue",
                       "thread_pool.index.queue", "thread_pool.search.queue", "thread_pool.force_merge.queue",
                       "thread_pool.bulk.rejected", "thread_pool.index.rejected", "thread_pool.search.rejected",
                       "thread_pool.force_merge.rejected", "fs.total.total_in_bytes", "fs.total.free_in_bytes",
                       "fs.total.available_in_bytes", "transport.rx_count", "transport.rx_size_in_bytes",
                       "transport.tx_count", "transport.tx_size_in_bytes", "transport.server_open",
                       "indices.segments.count"]

    # DEFAULT_INDICES = ["thread_pool.force_merge.rejected"]

    def __init__(self, config, filename, indices=DEFAULT_INDICES):
        self.indices = indices
        self.TAGKV = {}
        self.filename = filename
        self.addrdict = {}
        self.metrics_namespace_prefix = ""
        hosts = config['hosts']
        usename = config['username']
        password = config['password']
        use_ssl = config.get('use_ssl')

        self.client = Elasticsearch(hosts=hosts, http_auth=(usename, password), sniff_on_start=True,
                                    sniff_on_connection_fail=True,
                                    sniffer_timeout=60,
                                    use_ssl=use_ssl, verify_certs=False)

        self.define_tagkv()
        logger.info("init hosts={}".format(hosts))

    """
    https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-nodes-stats.html
    
    fs.timestamp
    fs.total.total_in_bytes
    fs.total.free_in_bytes
    
    
    os.cpu.percent
    os.cpu.load_average.1m
    os.cpu.load_average.5m
    os.cpu.load_average.15m
    os.mem.total_in_bytes
    os.mem.free_in_bytes
    os.mem.free_percent
    os.mem.used_in_bytes
    os.mem.used_percent
    os.swap.total_in_bytes
    os.swap.free_in_bytes
    os.swap.used_in_bytes
    
    https://www.jianshu.com/p/ec54c3bab79f
    
    indices.search.query_total
    indices.search.query_current 正在处理的查询量
    """

    def monitor(self):

        metrics.define_counter("indices.monitor.error", self.metrics_namespace_prefix)
        try:

            nodes_stats = self.client.nodes.stats()
            cluster_health = self.client.cluster.health()
            health_status = self.find(cluster_health, "status")
            if health_status == "green":
                health_code = 0
            elif health_status == "yellow":
                health_code = 1
            else:
                health_code = 2
            metrics.emit_store("cluster.health_status", health_code, prefix=self.metrics_namespace_prefix, tagkv={})
            nodes = json.loads(json.dumps(nodes_stats.get("nodes")))

            for node_name in nodes:
                node_value = nodes.get(node_name)
                if node_value is None:
                    continue
                tagv = self.addrdict.get(node_name)
                if tagv is None:
                    continue
                cur_tagk = {"instance": tagv}
                logger.info("cur_tagk={}".format(cur_tagk))
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

        try:
            publish_address_path = "http.publish_address"
            nodes_info = self.client.nodes.info()

            if nodes_info is None:
                return []
            cluster_name = self.find(nodes_info, "cluster_name")
            nodes_info = self.find(nodes_info, "nodes")
            tagv_arr = [self.filename]
            for node_name in nodes_info:
                node_value = nodes_info.get(node_name)
                publish_address = self.find(node_value, publish_address_path)
                tagv = publish_address.replace(".", "_").replace(":", "_")
                self.addrdict[node_name] = tagv
                tagv_arr.append(tagv)
            metrics.define_tagkv('instance', tagv_arr)
            self.metrics_namespace_prefix = '' + cluster_name
            metrics.define_store("cluster.health_status", self.metrics_namespace_prefix)
            for index in self.indices:
                metrics.define_store(index, self.metrics_namespace_prefix)
        except Exception as e:
            logger.warning(e)

    def find(self, json_info, path):
        segments = path.split('.')
        logger.debug("segments={}".format(segments))
        temp = dict(json_info)
        for segment in segments:

            temp = temp.get(segment)
            logger.debug("segment={},temp={}".format(segment, temp))
            if temp is None:
                return None

        logger.debug("segment={}, find value={}".format(segment, temp))
        return temp
