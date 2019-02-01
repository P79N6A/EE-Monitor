import logging
import jpype
from jpype import java
from jpype import javax
from anacapa.program import metrics

logger = logging.getLogger()

objectname_attr_dict = {
    "java.lang:type=Threading": ["ThreadCount"],
    "java.lang:type=OperatingSystem": ["SystemLoadAverage", "ProcessCpuLoad", "OpenFileDescriptorCount"],

    "org.apache.cassandra.metrics:type=ClientRequest,scope=Read,name=Latency": ["99thPercentile"],
    "org.apache.cassandra.metrics:type=ClientRequest,scope=Read,name=Failures": ["Count", "FiveMinuteRate"],
    "org.apache.cassandra.metrics:type=ClientRequest,scope=Read,name=Timeouts": ["Count", "FiveMinuteRate"],

    "org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Latency": ["99thPercentile"],
    "org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Failures": ["Count", "FiveMinuteRate"],
    "org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Timeouts": ["Count", "FiveMinuteRate"],

    "org.apache.cassandra.metrics:type=ClientRequest,scope=RangeSlice,name=Latency": ["99thPercentile"],
    "org.apache.cassandra.metrics:type=ClientRequest,scope=RangeSlice,name=Failures": ["Count", "FiveMinuteRate"],
    "org.apache.cassandra.metrics:type=ClientRequest,scope=RangeSlice,name=Timeouts": ["Count", "FiveMinuteRate"],

}


def isNumber(attr):
    try:
        float(attr)
        return True
    except Exception as e:
        return False


class CassandraMonitor():

    def __init__(self, config, filename):
        self.jmx_url = "service:jmx:rmi:///jndi/rmi://%s:%s/jmxrmi"
        self.hosts = config["hosts"]
        self.filename = filename
        self.all_nodes = set()
        self.metrics_namespace_prefix = 'ee.security.cluster_monitor' + '.cassandra.' + self.filename
        try:
            logger.info("jpype.getDefaultJVMPath={}".format(jpype.getDefaultJVMPath()))
            jpype.startJVM(jpype.getDefaultJVMPath())
            logger.info("JVM load OK")
            logger.info("hosts={}".format(self.hosts))
            # 根据提供的hosts列表找到所有的nodes 找到即可之后根据后续的nodes为准监控集群指标
            for host in self.hosts:
                ip, port = host.split(":")

                try:
                    connection_factory = self.get_connection_factory(ip, port)
                    connection = connection_factory.getMBeanServerConnection()
                    self.get_all_nodes(connection)
                    connection_factory.close()
                except Exception as e:
                    logger.exception(e)
                    continue
                finally:
                    pass
                logger.info("__init__ success,host={}, all_nodes={}".format(host, self.all_nodes))
                break


        except Exception as e:
            logger.error("CassandraMonitor init Connect Error!", e)

    def monitor(self):
        """
        question:https://stackoverflow.com/questions/7861299/jpype-doesnt-work-inside-thread
        :return:
        """
        jpype.attachThreadToJVM()
        metrics.define_counter("indices.monitor.error", self.metrics_namespace_prefix)
        for node in self.all_nodes:
            try:
                cur_tagk = {"instance": node.replace(".", "_").replace(":", "_")}
                connection_factory = self.get_connection_factory(node, "7199")
                connection = connection_factory.getMBeanServerConnection()
                logger.info("monitor,host={}".format(node))
                self.monitor_heap_usesage(node, connection)
                self.monitor_states(connection)
                logger.info("objectname_attr_dict={}".format(objectname_attr_dict))
                for object_name, attrs in objectname_attr_dict.items():
                    for attribute in attrs:
                        try:
                            attr_vlaue = connection.getAttribute(javax.management.ObjectName(object_name), attribute)
                        except Exception as e:
                            logger.info("monitor getAttribute ex,attribute={},exception={}".format(attribute, e))
                            continue
                        if isNumber(attr_vlaue) == False:
                            continue
                        object_name_path = self.build_path(object_name)
                        metrics.define_store(object_name_path + "." + attribute, self.metrics_namespace_prefix)
                        logger.info("monitor,object_name_path={},object_name={},attr_vlaue={}".format(object_name_path,
                                                                                                      object_name,
                                                                                                      attr_vlaue))
                        metrics.emit_store(object_name_path + "." + attribute, attr_vlaue,
                                           prefix=self.metrics_namespace_prefix, tagkv=cur_tagk)
            except Exception as e:
                logger.exception(e)
            finally:
                connection_factory.close()

    def get_connection_factory(self, ip, port, user=None, passsword=None):
        java_hash = java.util.HashMap()
        url = self.jmx_url % (ip, port)
        logger.debug("jmx_url={}".format(url))
        if user is not None and passsword is not None:
            java_array = jpype.JArray(java.lang.String)([user, passsword])
            java_hash.put(javax.management.remote.JMXConnector.CREDENTIALS, java_array);
        java_mxurl = javax.management.remote.JMXServiceURL(url)
        logger.debug("get_connection_factory complete!")
        return javax.management.remote.JMXConnectorFactory.connect(java_mxurl, java_hash)

    def build_path(self, object_name):
        domain, cn = object_name.split(":")
        kv_list = cn.split(",")
        list = []
        for v in kv_list:
            list.append(v.replace(" ", "_").split("=")[1])
        join = (".").join(list)
        path = domain + "." + join
        logger.debug("build_path={}".format(path))
        return path

    def get_all_nodes(self, connection):
        object_name = "org.apache.cassandra.net:type=FailureDetector"
        attr = "SimpleStates"
        simple_states = connection.getAttribute(javax.management.ObjectName(object_name), attr).toString()
        simple_states = simple_states.replace("{", "").replace("}", "").replace("/", "").split(", ")
        logger.info("simple_states={}".format(simple_states))
        tagv_list = []
        for item in simple_states:
            ip, status = item.split("=")
            self.all_nodes.add(ip)
            tagv = ip.replace(".", "_").replace(":", "_")
            tagv_list.append(tagv)
        metrics.define_tagkv('instance', tagv_list)

    def monitor_states(self, connection):
        logger.debug("enter monitor_states_and_get_nodes")
        object_name = "org.apache.cassandra.net:type=FailureDetector"
        attr = "SimpleStates"
        path = self.build_path(object_name)
        metrics.define_store(path + "." + attr, self.metrics_namespace_prefix)
        simple_states = connection.getAttribute(javax.management.ObjectName(object_name), attr).toString()
        simple_states = simple_states.replace("{", "").replace("}", "").replace("/", "").split(", ")
        attr_vlaue = 0
        logger.info("simple_states={}".format(simple_states))
        for item in simple_states:
            ip, status = item.split("=")
            self.all_nodes.add(ip)
            tagv = ip.replace(".", "_").replace(":", "_")
            cur_tagk = {"instance": tagv}
            if status != "UP":
                attr_vlaue = 1
            logger.info("ip={},SimpleStates={}".format(ip, status))
            metrics.emit_store(path + "." + attr, attr_vlaue, prefix=self.metrics_namespace_prefix, tagkv=cur_tagk)

    def monitor_heap_usesage(self, ip, connection):
        object_name = "java.lang:type=Memory"  # 查询内存
        path = self.build_path(object_name)
        attribute = "HeapMemoryUsage"
        metrics.define_store(path + "." + attribute, self.metrics_namespace_prefix)
        tagv = ip.replace(".", "_").replace(":", "_")
        cur_tagk = {"instance": tagv}
        attr = connection.getAttribute(javax.management.ObjectName(object_name), attribute)
        used = attr.contents.get("used")
        logger.debug("used={}".format(used))

        metrics.emit_store(path + "." + attribute, used, prefix=self.metrics_namespace_prefix, tagkv=cur_tagk)

    # def get_object_names(self, connection, domain):
    #     object_name_list = []
    #     for ele in connection.queryNames(javax.management.ObjectName(domain + ":*"), None):
    #         logger.debug("domain={},object_name={}".format(domain, ele.toString()))
    #         object_name_list.append(ele.toString())
    #     return object_name_list

    # def get_object_name_attributes(self, connection, object_name):
    #     obj = connection.getMBeanInfo(javax.management.ObjectName(object_name))
    #     object_name_attrs = []
    #     for element in obj.getAttributes():
    #         if False == element.isReadable():
    #             continue
    #         object_name_attrs.append(element.getName())
    #     return object_name_attrs

    # def get_object_name_attr_dict(self, connection):
    #     object_name_attr_dict = {}
    #     domain_list = self.get_domain(connection)
    #     for domain in domain_list:
    #         object_names = self.get_object_names(connection, domain)
    #         for object_name in object_names:
    #             attrs = self.get_object_name_attributes(connection, object_name)
    #             object_name_attr_dict[object_name] = attrs
    #
    #     return object_name_attr_dict

    # def get_domain(self, connection):
    #     domain_list = connection.getDomains()
    #     return domain_list
