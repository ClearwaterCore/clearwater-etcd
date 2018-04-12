import unittestgit
from mock import patch

from metaswitch.clearwater.queue_manager.timers import QueueTimer
from metaswitch.clearwater.queue_manager.queue_fsm import QueueFSM
from .plugin import TestNoTimerDelayPlugin

alarms_patch = patch("metaswitch.clearwater.queue_manager.alarms.alarm_manager")


class QueueFsmTest(unittest.TestCase):
    """Tests the QueueFsm."""
    def setUp(self):
        def dummy_callback():
            pass
        alarms_patch.start()
        self.plugin = TestNoTimerDelayPlugin()
        self.queue_fsm = QueueFSM(self.plugin, "test_fsm", dummy_callback)

    @patch.object(QueueTimer, "set")
    def test_waiting_on_other_node_error(self, mock_queue_timer_set):
        """Test that we set a local critical alarm and a timer for another node if we are in the
        errored state, waiting for another node."""
        queue_config = {"FORCE": "false",
                        "ERRORED": [{"ID": "10.0.0.1-node", "STATUS": "UNRESPONSIVE"}],
                        "COMPLETED": [],
                        "QUEUED": [{"ID": "10.0.0.2-node", "STATUS": "PROCESSING"}]
                        }
        self.queue_fsm.fsm_update(queue_config)

        mock_queue_timer_set.assert_called_once()
