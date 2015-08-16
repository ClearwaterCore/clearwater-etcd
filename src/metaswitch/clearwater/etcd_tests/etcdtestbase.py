from time import sleep
import logging
import sys
import etcd
from threading import Thread
import unittest
import json
from .utils.etcdserver import EtcdServer

from .utils.test_cluster_manager import TestClusterManager
from .utils.test_config_manager import TestConfigManager

logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logging.getLogger().setLevel(logging.INFO)

class EtcdTestBase(unittest.TestCase):
    def setUp(self):
        self.servers = {}
        self.config_manager = {}
        self.cluster_manager = {}

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

class GenericEtcdTests(EtcdTestBase):
    def restart_local_server(self):
        self.servers['127.0.0.101'].crash()
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

