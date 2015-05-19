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

_log = logging.getLogger("config_manager.etcd_synchronizer")


class EtcdSynchronizer(BaseEtcdSynchronizer):
    PAUSE_BEFORE_RETRY = 30

    def main(self):
        # Continue looping while the service is running.
        while not self._terminate_flag:
            # This blocks on changes to the watched key in etcd.
            _log.debug("Waiting for change from etcd for key{}".format(
                         self.plugin.key()))
            value = self.read_from_etcd()
            if self._terminate_flag:
                break

            if len(value) > 0:
                _log.debug("Got new config value from etcd:\n{}".format(value))
                self._plugin.on_config_changed(value, self._alarm)

    # Read the current value of the key from etcd (blocks until there's a
    # change).
    def read_from_etcd(self):
        self._read_from_etcd()
