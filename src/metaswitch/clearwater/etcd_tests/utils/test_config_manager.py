from metaswitch.clearwater.config_manager import plugin_base
from metaswitch.clearwater.config_manager.etcd_synchronizer import EtcdSynchronizer as CfgEtcdSynchronizer
from threading import Condition

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


class TestConfigManager(object):
    def __init__(self, etcd_ip):
        self.plugin = DummyCfgPlugin()
        self.s = CfgEtcdSynchronizer(self.plugin, etcd_ip, "local", None)
        self.s.start_thread()

    def value(self):
        return self.plugin.value

    def wait_for(self, *args, **kwargs):
        self.plugin.wait_for(*args, **kwargs)

    def stop(self):
        self.s.terminate()



