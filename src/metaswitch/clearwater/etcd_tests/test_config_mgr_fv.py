from .etcdtestbase import GenericEtcdTests

class ConfigMgrFVTest(GenericEtcdTests):
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

    def test_mainline(self):
        self.config_mgr_test(before_fn=None, during_fn=None)

    def test_local_server_restart(self):
        self.config_mgr_test(before_fn=None, during_fn=self.restart_local_server)

    def test_running_with_stopped_server(self):
        self.config_mgr_test(before_fn=self.stop_remote_server, during_fn=None)

    def test_abruptly_stopping_server(self):
        self.config_mgr_test(before_fn=None, during_fn=self.stop_remote_server)

    def test_adding_etcd_nodes(self):
        self.config_mgr_test(before_fn=None, during_fn=self.add_five_nodes)

    def test_1k_writes(self):
        self.config_mgr_test(before_fn=None, during_fn=self.restart_quorum)
