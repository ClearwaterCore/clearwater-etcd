import unittest
import logging
from mock import patch

from metaswitch.clearwater.queue_manager.timers import QueueTimer
from metaswitch.clearwater.queue_manager.queue_config import QueueConfig
from metaswitch.clearwater.queue_manager.queue_fsm import QueueFSM, QueueAlarm
from .plugin import TestNoTimerDelayPlugin

_log = logging.getLogger(__name__)

# Need to patch queue_manager.alarms.alarms_manager before any tests run, as it is an instance of
# _AlarmManager that gets imported in queue_manager.alarms.alarms
alarms_patch = patch("metaswitch.clearwater.queue_manager.alarms.alarm_manager")
alarms_patch.start()


def dummy_callback():
    pass


class QueueFsmStateTimersAndAlarmsTest (unittest.TestCase):
    def setUp(self):
        self.plugin = TestNoTimerDelayPlugin()

    @patch.object(QueueAlarm, "clear")
    @patch.object(QueueTimer, "set")
    def test_no_queue(self, mock_set_timer, mock_queue_alarm_clear):
        """
        Test that we clear a local and global critical alarm and don't set a timer if there is an
        empty queue (FSM state LS_NO_QUEUE).
        """
        queue_config = {"FORCE": "false",
                        "ERRORED": [],
                        "COMPLETED": [],
                        "QUEUED": []
                        }

        queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)
        queue_fsm.fsm_update(queue_config)

        assert mock_queue_alarm_clear.call_count == 2
        assert mock_set_timer.call_count == 0

    @patch.object(QueueAlarm, "critical")
    @patch.object(QueueTimer, "set")
    def test_no_queue_error(self, mock_set_timer, mock_queue_alarm_critical):
        """
        Test that we set a local and global critical alarm if we are in the errored state, with an
        empty queue (FSM state LS_NO_QUEUE_ERROR).
        """
        queue_config = {"FORCE": "false",
                        "ERRORED": [{"ID": "10.0.0.1-node", "STATUS": "UNRESPONSIVE"}],
                        "COMPLETED": [],
                        "QUEUED": []
                        }

        queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)
        queue_fsm.fsm_update(queue_config)

        assert mock_queue_alarm_critical.call_count == 2
        assert mock_set_timer.call_count == 0

    @patch.object(QueueConfig, "move_to_processing")
    @patch.object(QueueAlarm, "minor")
    @patch.object(QueueTimer, "set")
    def test_first_in_queue(self, mock_set_timer, mock_queue_alarm_minor, mock_move_to_processing):
        """
        Test that we set a minor local and global alarm and call move_to_processing if we are first
        in the queue (FSM state LS_FIRST_IN_QUEUE).
        """
        queue_config = {"FORCE": "false",
                        "ERRORED": [],
                        "COMPLETED": [],
                        "QUEUED": [{"ID": "10.0.0.1-node", "STATUS": "QUEUED"}]
                        }

        queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)
        queue_fsm.fsm_update(queue_config)

        assert mock_queue_alarm_minor.call_count == 2
        assert mock_move_to_processing.call_count == 1
        assert mock_set_timer.call_count == 0

    @patch.object(TestNoTimerDelayPlugin, "at_front_of_queue" )
    @patch.object(QueueAlarm, "minor")
    @patch.object(QueueTimer, "set")
    def test_processing(self, mock_set_timer, mock_queue_alarm_minor, mock_at_front_of_queue):
        """
        Test that we set a local and global minor alarm and call the plugin's at_front_of_queue
        method if we are processing (FSM state LS_PROCESSING).
        """
        queue_config = {"FORCE": "false",
                        "ERRORED": [],
                        "COMPLETED": [],
                        "QUEUED": [{"ID": "10.0.0.1-node", "STATUS": "PROCESSING"}]
                        }
        queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)
        queue_fsm.fsm_update(queue_config)

        assert mock_queue_alarm_minor.call_count == 2
        assert mock_at_front_of_queue.call_count == 1
        assert mock_set_timer.call_count == 0

    @patch.object(QueueAlarm, "minor")
    @patch.object(QueueAlarm, "clear")
    @patch.object(QueueTimer, "set")
    def test_waiting_on_other_node(self, mock_set_timer, mock_queue_alarm_clear, mock_queue_alarm_minor):
        """
        Test that we clear a local alarm, set a minor global alarm as well as a timer for another
        node if we are in the errored state, waiting for another node (FSM state
        LS_WAITING_ON_OTHER_NODE).
        """
        queue_config = {"FORCE": "false",
                        "ERRORED": [],
                        "COMPLETED": [],
                        "QUEUED": [{"ID": "10.0.0.2-node", "STATUS": "PROCESSING"}]
                        }

        queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)
        queue_fsm.fsm_update(queue_config)

        assert mock_queue_alarm_clear.call_count == 1
        assert mock_queue_alarm_minor.call_count == 1
        assert mock_set_timer.call_count == 1

    @patch.object(QueueAlarm, "critical")
    @patch.object(QueueTimer, "set")
    def test_waiting_on_other_node_error(self, mock_set_timer, mock_queue_alarm_critical):
        """
        Test that we set a local and global critical alarm as well as a timer for another node
        if we are in the errored state, waiting for another node (FSM state
        LS_WAITING_ON_OTHER_NODE_ERROR).
        """
        queue_config = {"FORCE": "false",
                        "ERRORED": [{"ID": "10.0.0.1-node", "STATUS": "UNRESPONSIVE"}],
                        "COMPLETED": [],
                        "QUEUED": [{"ID": "10.0.0.2-node", "STATUS": "PROCESSING"}]
                        }

        queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)
        queue_fsm.fsm_update(queue_config)

        assert mock_queue_alarm_critical.call_count == 2
        assert mock_set_timer.call_count == 1


class QueueFsmMethodsTest(unittest.TestCase):
    def setUp(self):
        self.plugin = TestNoTimerDelayPlugin()

    @patch.object(QueueTimer, "clear")
    def test_clear_timer_on_quit(self, mock_clear_timer):
        """Tests that the QueueFSM's timer gets cleared when quitting the QueueFSM."""
        queue_config = {"FORCE": "false",
                        "ERRORED": [],
                        "COMPLETED": [],
                        "QUEUED": [{"ID": "10.0.0.2-node", "STATUS": "PROCESSING"}]
                        }

        queue_fsm = QueueFSM(self.plugin, "10.0.0.1-node", dummy_callback)
        queue_fsm.fsm_update(queue_config)

        # QueueTimer.clear got called from QueueFSM.fsm_update when setting a timer for the node
        # that is processing. We are not interested in this call so we reset the mock here.
        mock_clear_timer.reset_mock()

        queue_fsm.quit()

        assert mock_clear_timer.call_count == 1
