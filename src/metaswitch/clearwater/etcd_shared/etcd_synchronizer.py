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

import etcd
from threading import Thread
from time import sleep

import urllib3
import logging

_log = logging.getLogger("etcd_shared.base_etcd_synchronizer")


class BaseEtcdSynchronizer(object):
    PAUSE_BEFORE_RETRY = 30

    def __init__(self, plugin, ip, alarm, etcd_ip=None):
        self._ip = ip
        if etcd_ip:
            self._client = etcd.Client(etcd_ip, 4000)
        else:
            self._client = etcd.Client(self._ip, 4000)
        self._plugin = plugin
        self._alarm = alarm
        self._index = None
        self._terminate_flag = False

    def should_terminate(self):
        return self._terminate_flag

    # Read the current value of the key from etcd (blocks until there's a
    # change).
    def _read_from_etcd(self, default=None):
        value = default

        try:
            result = self._client.get(self._plugin.key())

            # If the key hasn't changed since we last saw it, then
            # wait for it to change before doing anything else.
            _log.info("Read config value for {} from etcd (epoch {})".format(
                        self._plugin.key(),
                        result.modifiedIndex))

            if result.modifiedIndex == self._index:
                while not self.should_terminate():
                    try:
                        result = self._client.watch(self._plugin.key(),
                                                    index=result.modifiedIndex+1,
                                                    timeout=5,
                                                    recursive=False)
                        break
                    except urllib3.exceptions.TimeoutError:
                        # Timeouts after 5 seconds are expected, so ignore them
                        # - unless we're terminating, we'll stay in the while
                        # loop and try again
                        pass
                    except etcd.EtcdException as e:
                        # We have seen timeouts getting raised as EtcdExceptions
                        # so catch these here too and treat them as timeouts if
                        # they indicate that the read timed out.
                        if "Read timed out" in e.message:
                            pass
                        else:
                            raise
                    except ValueError:
                        # The index isn't valid to watch on, probably because
                        # there has been a snapshot between the get and the
                        # watch. Just start the read again.
                        _log.info("etcd index {} is invalid, retrying".format(
                            result.modifiedIndex+1))
                        self.read_from_etcd()

                # Return if we're terminating.
                if self._terminate_flag:
                    return

            # Save off the index of the result we're using for when we write
            # back to etcd later.
            self._index = result.modifiedIndex
            value = result.value

        except etcd.EtcdKeyError:
            # If the key doesn't exist in etcd then there is currently no
            # config.
            self._index = None
            pass
            pass
        except Exception as e:
            # Catch-all error handler (for invalid requests, timeouts, etc -
            # start over.
            _log.error("{} caught {!r} when trying to read with index {}"
                       " - pause before retry".
                       format(self._ip, e, self._index))
            # Sleep briefly to avoid hammering a failed server
            sleep(self.PAUSE_BEFORE_RETRY)
            # The main loop (which reads from etcd in a loop) should call this
            # function again after we return, causing the read to be retried
        return value
