#!/usr/bin/env python

# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

from metaswitch.clearwater.etcd_shared.test.mock_python_etcd import EtcdFactory
from metaswitch.clearwater.queue_manager.etcd_synchronizer import EtcdSynchronizer
from metaswitch.clearwater.queue_manager.timers import QueueTimer
from .plugin import TestNoTimerDelayPlugin
from mock import patch
from .test_base import BaseQueueTest

alarms_patch = patch("metaswitch.clearwater.queue_manager.alarms.alarm_manager")

class TimersTest(BaseQueueTest):
    @patch("etcd.Client", new=EtcdFactory)
    def setUp(self):
        alarms_patch.start()
        self._p = TestNoTimerDelayPlugin()
        self._e = EtcdSynchronizer(self._p, "10.0.0.1", "local", "clearwater", "node")

    @patch("metaswitch.clearwater.queue_manager.timers.QueueTimer")
    def test_no_timer_set_when_processing(self, mock_queue_timer):
        """Test that when a node is in processing state, it doesn't set a timer for itself."""
        # Write some initial data into the key
        self.set_initial_val("{\"FORCE\": false, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.1-node\",\"STATUS\":\"PROCESSING\"}]}")

        # As it is only one node, it keeps in the processing state as the plugin doesn't remove it
        # from the queue
        def pass_criteria(val):
            return (0 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (1 == len(val.get("QUEUED"))) and \
                   ("10.0.0.1-node" == val.get("QUEUED")[0]["ID"]) and \
                   ("PROCESSING" == val.get("QUEUED")[0]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))

        mock_queue_timer.clear.assert_not_called()

    def test_other_node_timer_pop(self):
        """Test that when a timer pops for another node it marks the other node as failed."""
        self.set_initial_val("{\"FORCE\": false, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.2-node\",\"STATUS\":\"PROCESSING\"}]}")

        def pass_criteria(val):
            return (1 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED"))) and \
                   ("10.0.0.2-node" == val.get("ERRORED")[0]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[0]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))

    def test_timer_pop_force(self):
        """Test that when a timer pops when force is true it doesn't clear the queue"""
        self.set_initial_val("{\"FORCE\": true, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.1-node\",\"STATUS\":\"PROCESSING\"},{\"ID\":\"10.0.0.2-node\",\"STATUS\":\"QUEUED\"}]}")

        self._e._fsm._timer = QueueTimer(self._e._fsm._timer_callback_func)
        self._e._fsm._timer.timer_popped = True

        def pass_criteria(val):
            return (2 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED"))) and \
                   ("10.0.0.1-node" == val.get("ERRORED")[0]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[0]["STATUS"]) and \
                   ("10.0.0.2-node" == val.get("ERRORED")[1]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[1]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))

    def test_timer_pop_no_force(self):
        """Test that when a timer pops when force is false it does clear the queue"""
        self.set_initial_val("{\"FORCE\": false, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.1-node\",\"STATUS\":\"PROCESSING\"},{\"ID\":\"10.0.0.2-node\",\"STATUS\":\"PROCESSING\"}]}")

        def pass_criteria(val):
            return (1 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED"))) and \
                   ("10.0.0.1-node" == val.get("ERRORED")[0]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[0]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))
