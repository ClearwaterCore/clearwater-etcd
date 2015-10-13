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

import re
import etcd
from time import sleep
from hashlib import md5

import urllib3
import logging

_log = logging.getLogger("config_manager.etcd_synchronizer")


class EtcdSynchronizer(object):
    PAUSE_BEFORE_RETRY = 30

    def __init__(self, plugin, ip, site, alarm):
        self._ip = ip
        self._site = site
        self._client = etcd.Client(self._ip, 4000)
        self._plugin = plugin
        self._alarm = alarm
        self._index = None
        self._terminate_flag = False

    def main(self):
        # Continue looping while the service is running.
        while not self._terminate_flag:
            # This blocks on changes to the watched key in etcd.
            _log.debug("Waiting for change from etcd for key {}".format(
                         self._plugin.key()))
            value = self.read_from_etcd()
            if self._terminate_flag:
                break

            if value:
                _log.info("Got new config value from etcd - filename {}, file size {}, MD5 hash {}".format(
                    self._plugin.file(),
                    len(value),
                    md5(value).hexdigest()))
                _log.debug("Got new config value from etcd:\n{}".format(value))
                self._plugin.on_config_changed(value, self._alarm)

    # Read the current value of the key from etcd (blocks until there's a
    # change).
    def read_from_etcd(self):
        value = None
        try:
            full_key = "/clearwater/" + self._site + "/configuration/" + self._plugin.key()

            result = None
            try:
                result = self._client.read(full_key, quorum=True)

                # If the key hasn't changed since we last saw it, then
                # wait for it to change before doing anything else.
                _log.info("Read config value for {} from etcd (epoch {})".format(
                            self._plugin.key(),
                            result.modifiedIndex))
            except etcd.EtcdKeyError:
                # If the key doesn't exist in etcd then there is currently no
                # config.
                _log.info("No config value for {} found".format(self._plugin.key()))
                self._index = None

            if result is None or result.modifiedIndex == self._index:
                while not self._terminate_flag:
                    _log.info("Watching for changes")
                    waitIndex = None if (self._index is None or result is None) else result.etcd_index + 1
                    result = self.waitHelper(full_key, waitIndex=waitIndex)
                    if result is not None:
                        break

                # Return if we're terminating.
                if self._terminate_flag:
                    return

            # Save off the index of the result we're using for when we write
            # back to etcd later.
            self._index = result.modifiedIndex
            value = result.value

        except Exception as e:
            # Catch-all error handler (for invalid requests, timeouts, etc -
            # start over.
            _log.error("{} caught {!r} when trying to read with index {}"
                       " - pause before retry".
                       format(self._ip, e, self._index))
            # Sleep briefly to avoid hammering a failed server
            sleep(self.PAUSE_BEFORE_RETRY)
            # The main loop (which reads from etcd in a loop) should call this
            # function again after we return, causing the read to be retried.

        return value

    def waitHelper(self, full_key, waitIndex):
        result = None
        # Calculate the args for the wait
        args = dict(wait=True,
                    timeout=0,
                    recursive=False)
        if waitIndex is not None:
            args['waitIndex'] = waitIndex

        try:
            # Wait for the key to change
            result = self._client.read(full_key,
                                       **args)
        except urllib3.exceptions.TimeoutError:
            # Timeouts after 5 seconds are expected, so ignore them
            # - unless we're terminating, we'll stay in the while
            # loop and try again
            pass
        except etcd.EtcdEventIndexCleared as e:
            # A snapshot has occurred since the last change, invalidating the
            # index, so wait again from the earliest index possible.

            # etcd doesn't pass the earliest index back in a structured way, but
            # we can parse it out of the error message.
            m = re.search("the requested history has been cleared [(\d+)/(\d+)]", e.message)
            new_index = m.group(1) if m is not None else None
            _log.info("An etcd snapshot has invalidated index %d - "
                      "starting a new watch with index %d",
                      args.get('waitIndex', None),
                      new_index)
            result = self.waitHelper(full_key, waitIndex=new_index)
        except etcd.EtcdException as e:
            # We have seen timeouts getting raised as EtcdExceptions
            # so catch these here too and treat them as timeouts if
            # they indicate that the read timed out.
            if "Read timed out" in e.message:
                pass
            else:
                raise
        return result
