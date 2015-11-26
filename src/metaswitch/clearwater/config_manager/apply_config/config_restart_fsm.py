# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015 Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

import constants

class SyncFSM(object):

    def __init__(self, plugin, node_id):
        self._plugin = plugin
        self._id = node_id
        self._running = True
        # Alarms? 

    def quit(self):
        self._alarm.quit()

    def is_running(self):
        return self._running

    # logging functions

    def next(self,
             old_local_state,
             old_global_state,
             new_apply_config):
        """Main state machine function.

        Arguments:
            - old_local_state: The current state of the node (before running through the FSM)
            - old_global_state: The node's current view of the state of the deployment (before running through the FSM)
            - apply_config: The current value in etcd

        Returns:
            - An updated apply_config (which the caller can decide whether to write back to etcd
        """
        # log entry values?
        assert(self._running)

        # Global state: NO_SYNC, SYNC, STOPPED_ERROR
        # Local state: WAITING, RESPONSE_TIMER, RESPONSE_TIMER_POPPED, PROCESSING,
        #              RESTART_TIMER, RESTART_TIMER_POPPED, SUCCESS

        # Local state is determined from the 
        # WAITING - Clear global alarm (nothing in the queue)
        # PROCESSING - Raise alarm (at the front of the queue in state queued)
        # RESTART_TIMER - Restart processes, kick off timer (at the front of the queue in state CHECKING)
        # RESTART_TIMER_POPPED - Abort, move to errored (at the front of the queue in state checking, restart timer indicates that it's been popped). Clear restart timer
        # RESPONSE_TIMER - Kick off timer (queue non empty, not at the front of it)
        # RESPONSE_TIMER_POPPED - Abort, move to errored (not at the front of the queue, response timer indicates that it's been popped). Clear restart timer
        # SUCCESS - For clearing the local alarm only. (at the front of the queue in state DONE)
        #
        # We work out what the updated apply_config should be given the local state of the node and return it
     
        # Get the new local/global state. We can detect the differences between TIMER/POPPED based on the state
        # of the timers.
        current_local_state, current_global_state, current_node_id, force = parse_current_json(apply_config)

        # We use the global state to raise/clear global alarms
        if old_global_state != new_global_state:
            if new_global_state == constants.NO_SYNC:
                # We've finished a resync operation (note, we shouldn't technically
                # support moving from STOPPED_ERROR to NO_SYNC, but we do because of
                # the clear_config_apply tool
                self._global_alarm.clear()
                self._local_alarm.clear() # Needed because of tool (as we could have jumped straight to this state)
            elif new_global_state == constants.SYNC:
                # We've started  a resync operation
                self._global_alarm.minor()
            else:
                # A resync operation has stopped with errors
	        if old_global_state == constants.NO_SYNC:
                    # We shouldn't have got here - log this
 
                self._global_alarm.critical()

        # Now look at the local state. We only look at the old local state to log if we've
        # done anything strange in terms of moving local states. If something has gone wrong
        # the behaviour is just to log, and continue as expected given the new local state
        if new_local_state == old_local_state:
            # Probably nothing to do here - the exception is that we may want to reset the timer
            if new_local_state == constants.RESPONSE_TIMER:
                self._response_timer.set(current_node_id)
                return apply_config
        else:
            if new_local_state == constants.WAITING:
                # Any previous state here is valid because of the clear_apply_config tool
                return apply_config
            elif new_local_state == constants.PROCESSING: # Any old state is valid here
                # Raise alarm and move to restart timer state
                self._local_alarm.minor()
                # update apply_config
                return apply_config
            elif new_local_state == constants.RESTART_TIMER: # Expect processing to start
                # Restart processes, kick off timer
                self._restart_timer.set()
                return apply_config
            elif new_local_state == constants.SUCCESS:
                # Restart processes, kick off timer
                self._restart_timer.clear()
                self._local_alarm.clear()
                # Remove node from queue
                return apply_config
            elif new_local_state == constants.RESTART_TIMER_POPPED:
                self._local_alarm.critical()
                self._restart_timer.clear()
                # Set the new apply config - exact JSON depends on the value of force
                return apply_config
            elif new_local_state == constants.RESPONSE_TIMER:
                self._response_timer.set(current_node_id)
                return apply_config
            elif new_local_state == constants.RESPONSE_TIMER_POPPED:
                self._global_alarm.critical()
                self._response_timer.clear()                          
                # Set the new apply config - exact JSON depends on the value of force
                return apply_config
