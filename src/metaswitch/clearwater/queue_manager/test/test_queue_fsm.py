import unittest
from mock import patch

from metaswitch.clearwater.queue_manager.timers import QueueTimer
from metaswitch.clearwater.queue_manager.queue_fsm import QueueFSM
from .plugin import TestNoTimerDelayPlugin

import logging
_log = logging.getLogger(__name__)

# Need to patch queue_manager.alarms.alarms_manager before any tests run, as it is an instance of
# _AlarmManager that gets imported in queue_manager.alarms.alarms
alarms_patch = patch("metaswitch.clearwater.queue_manager.alarms.alarm_manager")
alarms_patch.start()

queue_alarm_patch = patch("metaswitch.clearwater.queue_manager.queue_fsm.QueueAlarm")


class QueueFsmTest(unittest.TestCase):
    """Tests the QueueFsm."""
    def setUp(self):
        def dummy_callback():
            pass

        self.plugin = TestNoTimerDelayPlugin()

        # Need to patch queue_fsm.QueueAlarm before creating a QueueFSM
        self.mock_queue_alarm = queue_alarm_patch.start()

        self.queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)

    @patch.object(QueueTimer, "set")
    def test_waiting_on_other_node_error(self, mock_queue_timer_set):
        """Test that we set a local and global critical alarm as well as a timer for another node
        if we are in the errored state, waiting for another node."""
        queue_config = {"FORCE": "false",
                        "ERRORED": [{"ID": "10.0.0.1-node", "STATUS": "UNRESPONSIVE"}],
                        "COMPLETED": [],
                        "QUEUED": [{"ID": "10.0.0.2-node", "STATUS": "PROCESSING"}]
                        }
        self.queue_fsm.fsm_update(queue_config)

        # We have mocked queue_fsm
        assert len(self.queue_fsm._local_alarm.method_calls) == 2
        mock_queue_timer_set.assert_called_once()
