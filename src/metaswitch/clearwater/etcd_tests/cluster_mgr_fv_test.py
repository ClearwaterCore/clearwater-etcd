from .etcdtestbase import GenericEtcdTests

class ClusterMgrFVTest(GenericEtcdTests):
    def cluster_mgr_test(self, before_fn, during_fn):
        ips = ['127.0.0.100', '127.0.0.101', '127.0.0.102']
        self.initialise_servers(*ips)
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
        self.cluster_mgr_test(before_fn=None, during_fn=None)

    def test_single_server_restart(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.restart_local_server)

    def test_quorum_restart(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.restart_quorum)

    def test_adding_etcd_nodes(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.add_five_nodes)

    def test_1k_writes(self):
        self.cluster_mgr_test(before_fn=None, during_fn=self.do_1k_writes)
