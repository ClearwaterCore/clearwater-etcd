from metaswitch.clearwater.config_manager.etcd_synchronizer import EtcdSynchronizer
from time import sleep
import logging
import sys
import etcd
from threading import Thread
import unittest

from dummy_cfg_plugin import DummyCfgPlugin
from etcdserver import EtcdServer

logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logging.getLogger().setLevel(logging.ERROR)

class TestConfigManager(object):
    def __init__(self, etcd_ip):
        self.plugin = DummyCfgPlugin()
        self.s = EtcdSynchronizer(self.plugin, etcd_ip, "local", None)
        self.thread = Thread(target=self.s.main)
        self.thread.daemon = True
        self.thread.start()

    def value(self):
        return self.plugin.value

    def wait_for(self, *args, **kwargs):
        self.plugin.wait_for(*args, **kwargs)

    def stop(self):
        self.s._terminate_flag = True


class EtcdTestBase(unittest.TestCase):
    def __init__(self, x):
        self.servers = {}
        self.config_manager = {}
        unittest.TestCase.__init__(self, x)

    def add_server(self, ip, **kwargs):
        server = EtcdServer(ip, **kwargs)
        self.servers[ip] = server

    def initialise_servers(self, *args):
        ip0 = args[0]
        self.add_server(ip0)
        for ip in args[1:]:
            self.add_server(ip, existing=ip0)

    def add_config_manager(self, etcd_ip):
        mgr = TestConfigManager(etcd_ip)
        self.config_manager[etcd_ip] = mgr
        return mgr

    def tearDown(self):
        print "Tearing down!"
        for client in self.config_manager.values():
            client.stop()
        for server in self.servers.values():
            server.crash()
        EtcdServer.delete_datadir()

    def delay_one_second(self, fn, *args, **kwargs):
        def inner():
            sleep(1)
            fn(*args, **kwargs)
        Thread(target=inner).start()

    def restart_local_server(self):
        self.servers['127.0.0.101'].crash()
        #self.add_server('127.0.0.101', existing='127.0.0.100', replacement=True)
        self.delay_one_second(self.add_server, '127.0.0.101', existing='127.0.0.100', replacement=True)

    def restart_remote_server(self):
        self.servers['127.0.0.102'].crash()
        self.add_server('127.0.0.102', existing='127.0.0.100', replacement=True)

    def stop_remote_server(self):
        self.servers['127.0.0.102'].crash()
        del self.servers['127.0.0.102']
        sleep(0.2)

    def config_mgr_test(self, before_fn, during_fn):
        # Check that a write is picked up
        self.initialise_servers('127.0.0.100', '127.0.0.101', '127.0.0.102')

        if before_fn:
            before_fn()

        mgr = self.add_config_manager('127.0.0.101')
        client = self.servers['127.0.0.100'].client()

        client.write("/clearwater/local/configuration//dummy/", "hello world")
        mgr.wait_for('hello world', 35)
        self.assertEqual(mgr.value(), "hello world")

        if during_fn:
            during_fn()

        client.write("/clearwater/local/configuration//dummy/", "hello world 2")
        mgr.wait_for('hello world 2', 35)
        self.assertEqual(mgr.value(), "hello world 2")

    def test_one(self):
        self.config_mgr_test(before_fn=None, during_fn=None)

    def test_two(self):
        self.config_mgr_test(before_fn=None, during_fn=self.restart_local_server)

    def test_three(self):
        self.config_mgr_test(before_fn=self.stop_remote_server, during_fn=None)

    def test_four(self):
        self.config_mgr_test(before_fn=None, during_fn=self.stop_remote_server)
