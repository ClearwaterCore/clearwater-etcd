from metaswitch.clearwater.config_manager.etcd_synchronizer import EtcdSynchronizer as CfgEtcdSynchronizer
from metaswitch.clearwater.cluster_manager.etcd_synchronizer import EtcdSynchronizer as ClusterEtcdSynchronizer
from time import sleep
import logging
import sys
import etcd
from threading import Thread
import unittest
import json

from dummy_cfg_plugin import DummyCfgPlugin, DummyClusterPlugin
from etcdserver import EtcdServer

logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logging.getLogger().setLevel(logging.ERROR)

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



class EtcdTestBase(unittest.TestCase):
    def __init__(self, x):
        self.servers = {}
        self.config_manager = {}
        self.cluster_manager = {}
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

    def add_cluster_manager(self, etcd_ip, fn=None):
        mgr = TestClusterManager(etcd_ip, fn)
        self.cluster_manager[etcd_ip] = mgr
        return mgr

    def tearDown(self):
        print "Tearing down!"
        for client in self.config_manager.values():
            client.stop()
        for client in self.cluster_manager.values():
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

    def restart_quorum(self):
        self.servers['127.0.0.101'].crash()
        self.servers['127.0.0.102'].crash()
        self.delay_one_second(self.add_server, '127.0.0.101', existing='127.0.0.100', replacement=True)
        self.delay_one_second(self.add_server, '127.0.0.102', existing='127.0.0.100', replacement=True)

    def add_five_nodes(self):
        for ip in ['127.0.0.200',
                   '127.0.0.201',
                   '127.0.0.202',
                   '127.0.0.203',
                   '127.0.0.204']:
            self.add_server(ip, existing='127.0.0.100')

    def stop_remote_server(self):
        self.servers['127.0.0.102'].crash()
        del self.servers['127.0.0.102']
        sleep(0.2)

    def do_1k_writes(self):
        client = self.servers['127.0.0.100'].client()

        for i in range(1001):
            client.write("/foobar/", str(i))

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

    def cluster_mgr_test(self, before_fn, during_fn):
        self.initialise_servers('127.0.0.100', '127.0.0.101', '127.0.0.102')
        client = self.servers['127.0.0.100'].client()
        client.write("/dummy/", "{}")

        if before_fn:
            before_fn()

        mgr1 = self.add_cluster_manager('127.0.0.100')

        mgr2 = self.add_cluster_manager('127.0.0.101', during_fn)
        mgr3 = self.add_cluster_manager('127.0.0.102')

        expected = {'127.0.0.100': 'normal',
                    '127.0.0.101': 'normal',
                    '127.0.0.102': 'normal'}

        mgr1.wait_for(expected)
        mgr2.wait_for(expected)

        self.assertEqual(mgr1.value(), expected)
        self.assertEqual(mgr2.value(), expected)

        # Don't assert anything about mgr3 - we may have killed that server


    def test_one(self):
        self.config_mgr_test(before_fn=None, during_fn=None)

    def test_two(self):
        self.config_mgr_test(before_fn=None, during_fn=self.restart_local_server)

    def test_three(self):
        self.config_mgr_test(before_fn=self.stop_remote_server, during_fn=None)

    def test_four(self):
        self.config_mgr_test(before_fn=None, during_fn=self.stop_remote_server)

    def test_four_a(self):
        self.config_mgr_test(before_fn=None, during_fn=self.add_five_nodes)

    def test_four_b(self):
        self.config_mgr_test(before_fn=None, during_fn=self.restart_quorum)

    def test_five(self):
        self.cluster_mgr_test(before_fn=None, during_fn=None)

    def test_six(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.restart_local_server)

    def test_seven(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.restart_quorum)

    def test_eight(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.add_five_nodes)

    def test_nine(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.do_1k_writes)
