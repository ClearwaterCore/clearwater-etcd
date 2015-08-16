from metaswitch.clearwater.cluster_manager.etcd_synchronizer import EtcdSynchronizer as ClusterEtcdSynchronizer
from metaswitch.clearwater.cluster_manager.plugin_base import SynchroniserPluginBase
from time import sleep

class DummyClusterPlugin(SynchroniserPluginBase):
    def __init__(self, fn):
        self.value = None
        self.fn = fn

    def key(self):
        return "/dummy/"

    def on_cluster_changing(self, cluster_view):
        self.value = cluster_view

    def on_joining_cluster(self, cluster_view):
        self.on_cluster_changing(cluster_view)

    def on_new_cluster_config_ready(self, cluster_view):
        if self.fn:
            self.fn()
            self.fn = None
        self.on_cluster_changing(cluster_view)

    def on_stable_cluster(self, cluster_view):
        self.on_cluster_changing(cluster_view)

    def on_leaving_cluster(self, cluster_view):
        self.on_cluster_changing(cluster_view)

    def wait_for(self, value, timeout=300):
        for i in range(timeout):
            if self.value != value:
                sleep(1)



class TestClusterManager(object):
    def __init__(self, etcd_ip, during_fn):
        self.plugin = DummyClusterPlugin(during_fn)
        self.s = ClusterEtcdSynchronizer(self.plugin, etcd_ip, pause_before_retry=2, fsm_delay=1)
        self.s.start_thread()

    def value(self):
        return self.plugin.value

    def wait_for(self, *args, **kwargs):
        self.plugin.wait_for(*args, **kwargs)

    def stop(self):
        self.s.terminate()



