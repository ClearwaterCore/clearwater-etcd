import logging
import os
import signal
from metaswitch.clearwater.cluster_manager import constants

_log = logging.getLogger("memcached_plugin")


def write_cluster_settings(filename, cluster_view):
    valid_servers_states = [constants.LEAVING_ACKNOWLEDGED_CHANGE,
                            constants.LEAVING_CONFIG_CHANGED,
                            constants.NORMAL_ACKNOWLEDGED_CHANGE,
                            constants.NORMAL_CONFIG_CHANGED,
                            constants.NORMAL]
    valid_new_servers_states = [constants.NORMAL_ACKNOWLEDGED_CHANGE,
                                constants.NORMAL_CONFIG_CHANGED,
                                constants.JOINING_ACKNOWLEDGED_CHANGE,
                                constants.JOINING_CONFIG_CHANGED]
    servers_ips = sorted([k for k, v in cluster_view.iteritems()
                          if v in valid_servers_states])

    new_servers_ips = sorted([k for k, v in cluster_view.iteritems()
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
    with open(filename) as f:
        f.write(new_file_contents)


def send_sighup(pidfile):
    with open(pidfile) as f:
        pid = int(f.read())
        os.kill(pid, signal.SIGHUP)