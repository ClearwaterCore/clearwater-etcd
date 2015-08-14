from metaswitch.clearwater.config_manager import plugin_base
from metaswitch.clearwater.cluster_manager.plugin_base import SynchroniserPluginBase

from threading import Condition
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

class DummyCfgPlugin(plugin_base.ConfigPluginBase):
    def __init__(self):
        self.value = None
        self.condvar = Condition()

    def key(self):
        return "/dummy/"

    def file(self):
        return "/dummy.json"

    def status(self, value):
        if value == self.value:
            return plugin_base.FileStatus.UP_TO_DATE
        elif self.value is None:
            return plugin_base.FileStatus.MISSING
        else:
            return plugin_base.FileStatus.OUT_OF_SYNC

    def on_config_changed(self, value, alarm):
        print "Config changed: {} -> {}".format(self.value, value)
        self.condvar.acquire()
        self.value = value
        self.condvar.notifyAll()
        self.condvar.release()

    def wait_for(self, expected, timeout=30):
        self.condvar.acquire()
        if self.value != expected:
            self.condvar.wait(timeout)
        self.condvar.release()
