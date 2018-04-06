#!/usr/bin/env python

# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

from metaswitch.clearwater.etcd_shared.test.mock_python_etcd import EtcdFactory
from metaswitch.clearwater.queue_manager.etcd_synchronizer import EtcdSynchronizer
from metaswitch.clearwater.queue_manager.null_plugin import NullPlugin
from .plugin import TestNoTimerDelayPlugin, TestRemoveFromQueueAfterProcessingPlugin
from mock import patch
from .test_base import BaseQueueTest

alarms_patch = patch("metaswitch.clearwater.queue_manager.alarms.alarm_manager")

class TimersTest(BaseQueueTest):
    @patch("etcd.Client", new=EtcdFactory)
    def setUp(self):
        alarms_patch.start()
        self._p = TestNoTimerDelayPlugin()
        self._e = EtcdSynchronizer(self._p, "10.0.0.1", "local", "clearwater", "node")

    # Test that when a timer pops for the current node it marks the node as failed
    def test_this_node_timer_pop(self):
        # Write some initial data into the key
        self.set_initial_val("{\"FORCE\": false, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.1-node\",\"STATUS\":\"PROCESSING\"}]}")

        def pass_criteria(val):
            return (1 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED"))) and \
                   ("10.0.0.1-node" == val.get("ERRORED")[0]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[0]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))

    @patch("etcd.Client", new=EtcdFactory)
    # Test that when a timer pops for another node it marks the other node as failed
    def test_other_node_timer_pop(self):
        # Write some initial data into the key
        self.set_initial_val("{\"FORCE\": false, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.2-node\",\"STATUS\":\"PROCESSING\"}]}")

        def pass_criteria(val):
            return (1 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED"))) and \
                   ("10.0.0.2-node" == val.get("ERRORED")[0]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[0]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))

    # Test that when a timer pops when force is true it doesn't clear the queue
    def test_timer_pop_force(self):
        # Write some initial data into the key
        self.set_initial_val("{\"FORCE\": true, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.1-node\",\"STATUS\":\"PROCESSING\"},{\"ID\":\"10.0.0.2-node\",\"STATUS\":\"QUEUED\"}]}")

        def pass_criteria(val):
            return (2 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED"))) and \
                   ("10.0.0.1-node" == val.get("ERRORED")[0]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[0]["STATUS"]) and \
                   ("10.0.0.2-node" == val.get("ERRORED")[1]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[1]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))

    # Test that when a timer pops when force is false it does clear the queue
    def test_timer_pop_no_force(self):
        # Write some initial data into the key
        self.set_initial_val("{\"FORCE\": false, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.1-node\",\"STATUS\":\"PROCESSING\"},{\"ID\":\"10.0.0.2-node\",\"STATUS\":\"PROCESSING\"}]}")

        def pass_criteria(val):
            return (1 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED"))) and \
                   ("10.0.0.1-node" == val.get("ERRORED")[0]["ID"]) and \
                   ("UNRESPONSIVE" == val.get("ERRORED")[0]["STATUS"])

        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))


class SucessfulProcessingTimersTest(BaseQueueTest):
    """Test cases for when nodes successfully finish processing."""
    @patch("etcd.Client", new=EtcdFactory)
    def setUp(self):
        alarms_patch.start()
        null_etcd_synchronizer = EtcdSynchronizer(NullPlugin("queue_test"), "10.0.0.1", "local",
                                                  "clearwater", "node")
        self._p = TestRemoveFromQueueAfterProcessingPlugin(null_etcd_synchronizer)
        self._e = EtcdSynchronizer(self._p, "10.0.0.1", "local", "clearwater", "node")

    @patch("metaswitch.clearwater.queue_manager.timers.QueueTimer")
    def test_timer_gets_cancelled(self, mock_queue_timer):
        """Tests that a node cancels its own timer once it finishes processing."""
        # Add node as processing to front of queue
        self.set_initial_val("{\"FORCE\": false, \"ERRORED\": [], \"COMPLETED\": [], \"QUEUED\": [{\"ID\":\"10.0.0.1-node\",\"STATUS\":\"PROCESSING\"}]}")

        # Check that the node removes itself from the queue after finishing processing.
        def pass_criteria(val):
            return (0 == len(val.get("ERRORED"))) and \
                   (0 == len(val.get("COMPLETED"))) and \
                   (0 == len(val.get("QUEUED")))
        self.assertTrue(self.wait_for_success_or_fail(pass_criteria))

        # Once the node finished processing the timer should get cleared to join the timer thread
        # and then set to None.
        mock_queue_timer.clear.assert_called_once()

        timer = self._e._fsm._timer
        self.assertTrue(timer is None)
