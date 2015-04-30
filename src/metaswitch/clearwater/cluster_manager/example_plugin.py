from metaswitch.clearwater.cluster_manager.plugin_base import SynchroniserPluginBase
import logging

_log = logging.getLogger("example_plugin")


class ExamplePlugin(SynchroniserPluginBase):
    def __init__(self):
        _log.debug("Raising not-clustered alarm")

    def on_cluster_changing(self, cluster_view):
        _log.debug("New view of the cluster is {}".format(cluster_view))

    def on_joining_cluster(self, cluster_view):
        _log.info("I'm about to join the cluster")

    def on_new_cluster_config_ready(self, cluster_view):
        _log.info("All nodes have updated configuration")

    def on_stable_cluster(self, cluster_view):
        _log.info("Cluster is stable")
        _log.debug("Clearing not-clustered alarm")

    def on_leaving_cluster(self, cluster_view):
        _log.info("I'm out of the cluster")


def load_as_plugin():
    return ExamplePlugin()

print load_as_plugin()
