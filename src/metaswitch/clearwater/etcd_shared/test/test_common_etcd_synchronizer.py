import unittest
from mock import patch, Mock, MagicMock

from metaswitch.clearwater.etcd_shared.common_etcd_synchronizer import CommonEtcdSynchronizer
from metaswitch.clearwater.queue_manager.null_plugin import NullPlugin

alarms_patch = patch("metaswitch.clearwater.queue_manager.alarms.alarm_manager")


class CommonEtcdSynchronizerTest(unittest.TestCase):
    def setUp(self):
        alarms_patch.start()

    def test_read_from_etcd_with_abort_read_true(self):
        """
        When an implementation of CommonEtcdSynchronizer aborts a read (by setting _abort_read
        to True), any subsequent read should return the last value it got.
        This is used when another thread got triggered to take over the control flow (e.g. triggered
        by a popped timer).
        """
        plugin = NullPlugin("/test")
        common_etcd_synchronizer = CommonEtcdSynchronizer(plugin, "10.0.0.1")

        mock_etcd_client = MagicMock()
        mock_etcd_client.read.return_value = Mock(etcd_index=0)

        common_etcd_synchronizer._client = mock_etcd_client
        common_etcd_synchronizer.key = lambda : "test_key"
        common_etcd_synchronizer._abort_read = True
        common_etcd_synchronizer._last_value = "last_value_test"
        common_etcd_synchronizer._index = "index_test"

        result = common_etcd_synchronizer.read_from_etcd(wait=False)
        assert result == ("last_value_test", "index_test")
