import unittest
from mock import patch, Mock

from metaswitch.clearwater.etcd_shared.common_etcd_synchronizer import CommonEtcdSynchronizer
from metaswitch.clearwater.queue_manager.null_plugin import NullPlugin

alarms_patch = patch("metaswitch.clearwater.queue_manager.alarms.alarm_manager")


class CommonEtcdSynchronizerTest(unittest.TestCase):
    def setUp(self):
        alarms_patch.start()

    def test_read(self):
        """Test that CommonEtcdSynchronizer.read_from_etcd returns the correct result if the
        _abort_read flag is set."""
        plugin = NullPlugin("/test")
        common_etcd_synchronizer = CommonEtcdSynchronizer(plugin, "10.0.0.1")

        mock_etcd_client = Mock()
        attrs = {'read.return_value': Mock(etcd_index=0)}
        mock_etcd_client.configure_mock(**attrs)
        common_etcd_synchronizer._client = mock_etcd_client

        def return_test_key():
            return "test_key"
        common_etcd_synchronizer.key = return_test_key

        common_etcd_synchronizer._abort_read = True
        common_etcd_synchronizer._last_value = "last_value_test"
        common_etcd_synchronizer._index = "index_test"

        result = common_etcd_synchronizer.read_from_etcd(wait=False)
        assert result == ("last_value_test", "index_test")
