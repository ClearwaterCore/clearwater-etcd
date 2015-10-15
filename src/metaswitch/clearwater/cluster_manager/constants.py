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


# Cluster states
EMPTY = "empty"
STABLE = "stable"
STABLE_WITH_ERRORS = "stable with errors"
JOIN_PENDING = "join pending"
STARTED_JOINING = "started joining"
JOINING_CONFIG_CHANGING = "joining, config changing"
JOINING_RESYNCING = "joining, resyncing"
LEAVE_PENDING = "leave pending"
STARTED_LEAVING = "started leaving"
LEAVING_CONFIG_CHANGING = "leaving, config changing"
LEAVING_RESYNCING = "leaving, resyncing"
FINISHED_LEAVING = "finished leaving"
INVALID_CLUSTER_STATE = "invalid cluster state"

# Node states
WAITING_TO_JOIN = "waiting to join"
JOINING = "joining"
JOINING_ACKNOWLEDGED_CHANGE = "joining, acknowledged change"
JOINING_CONFIG_CHANGED = "joining, config changed"
NORMAL = "normal"
NORMAL_ACKNOWLEDGED_CHANGE = "normal, acknowledged change"
NORMAL_CONFIG_CHANGED = "normal, config changed"
WAITING_TO_LEAVE = "waiting to leave"
LEAVING = "leaving"
LEAVING_ACKNOWLEDGED_CHANGE = "leaving, acknowledged change"
LEAVING_CONFIG_CHANGED = "leaving, config changed"
FINISHED = "finished"
ERROR = "error"

# Alarm entries
RAISE_TOO_LONG_CLUSTERING = "8000.4"
CLEAR_TOO_LONG_CLUSTERING = "8000.1"

RAISE_MEMCACHED_NOT_YET_CLUSTERED = "8002.4"
CLEAR_MEMCACHED_NOT_YET_CLUSTERED = "8002.1"

RAISE_CHRONOS_NOT_YET_CLUSTERED = "8001.4"
CLEAR_CHRONOS_NOT_YET_CLUSTERED = "8001.1"

RAISE_CASSANDRA_NOT_YET_CLUSTERED = "8003.4"
CLEAR_CASSANDRA_NOT_YET_CLUSTERED = "8003.1"
RAISE_CASSANDRA_NOT_YET_DECOMMISSIONED = "8004.4"
CLEAR_CASSANDRA_NOT_YET_DECOMMISSIONED = "8004.1"
