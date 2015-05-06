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


import logging
from textwrap import dedent
import subprocess
from metaswitch.clearwater.cluster_manager import constants

_log = logging.getLogger("cluster_manager.plugin_utils")


def write_memcached_cluster_settings(filename, cluster_view):
    """Writes out the memcached cluster_settings file"""
    valid_servers_states = [constants.LEAVING_ACKNOWLEDGED_CHANGE,
                            constants.LEAVING_CONFIG_CHANGED,
                            constants.NORMAL_ACKNOWLEDGED_CHANGE,
                            constants.NORMAL_CONFIG_CHANGED,
                            constants.NORMAL]
    valid_new_servers_states = [constants.NORMAL,
                                constants.NORMAL_ACKNOWLEDGED_CHANGE,
                                constants.NORMAL_CONFIG_CHANGED,
                                constants.JOINING_ACKNOWLEDGED_CHANGE,
                                constants.JOINING_CONFIG_CHANGED]
    servers_ips = sorted(["{}:11211".format(k)
                          for k, v in cluster_view.iteritems()
                          if v in valid_servers_states])

    new_servers_ips = sorted(["{}:11211".format(k)
                              for k, v in cluster_view.iteritems()
                              if v in valid_new_servers_states])

    new_file_contents = ""
    if new_servers_ips == servers_ips:
        new_file_contents = "servers={}\n".format(",".join(servers_ips))
    else:
        new_file_contents = "servers={}\nnew_servers={}\n".format(
            ",".join(servers_ips),
            ",".join(new_servers_ips))

    _log.debug("Writing out cluster_settings file '{}'".format(
        new_file_contents))
    with open(filename, "w") as f:
        f.write(new_file_contents)


def run_command(command):
    """Runs the given shell command, logging the output and return code"""
    try:
        output = subprocess.check_output(command,
                                         shell=True,
                                         stderr=subprocess.STDOUT)
        _log.info("Command {} succeeded and printed output {!r}".
                  format(command, output))
        return 0
    except subprocess.CalledProcessError as e:
        _log.error("Command {} failed with return code {}"
                   " and printed output {!r}".format(command,
                                                     e.returncode,
                                                     e.output))
        return e.returncode


def write_chronos_cluster_settings(filename, cluster_view, current_server):
    current_or_joining = [constants.JOINING_ACKNOWLEDGED_CHANGE,
                          constants.JOINING_CONFIG_CHANGED,
                          constants.NORMAL_ACKNOWLEDGED_CHANGE,
                          constants.NORMAL_CONFIG_CHANGED,
                          constants.NORMAL]
    leaving = [constants.LEAVING_ACKNOWLEDGED_CHANGE,
               constants.LEAVING_CONFIG_CHANGED]

    staying_servers = ([k for k, v in cluster_view.iteritems()
                        if v in current_or_joining])
    leaving_servers = ([k for k, v in cluster_view.iteritems()
                        if v in leaving])

    with open(filename, 'w') as f:
        f.write(dedent('''\
        [cluster]
        localhost = {}
        ''').format(current_server))
        for node in staying_servers:
            f.write('node = {}\n'.format(node))
        for node in leaving_servers:
            f.write('leaving = {}\n'.format(node))
