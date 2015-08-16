from subprocess import Popen, PIPE
import httplib
import json
from time import sleep
from signal import SIGTERM
import shlex
import etcd
from shutil import rmtree

first_cmd = """clearwater-etcd/usr/bin/etcd --listen-client-urls http://{0}:4000 --advertise-client-urls http://{0}:4000 --listen-peer-urls http://{0}:2380 --initial-advertise-peer-urls http://{0}:2380 --initial-cluster-state new --initial-cluster {1}=http://{0}:2380 --data-dir {2}/{1} --name {1}"""
subsequent_cmd = """clearwater-etcd/usr/bin/etcd --listen-client-urls http://{0}:4000 --advertise-client-urls http://{0}:4000 --listen-peer-urls http://{0}:2380 --initial-advertise-peer-urls http://{0}:2380 --initial-cluster-state existing --initial-cluster {3} --data-dir {2}/{1} --name {1}"""

class EtcdServer(object):
    datadir = "./etcd_test_data"


    @classmethod
    def delete_datadir(cls):
        rmtree(cls.datadir)

    def __init__(self, ip, existing=None, replacement=False):
        self._ip = ip
        name = ip.replace(".", "-")

        if existing is None:
            self._subprocess = Popen(shlex.split(first_cmd.format(ip, name, EtcdServer.datadir)),
                                     #stdout=PIPE,
                                     #stderr=PIPE
                                     )
        else:
            own_data = {"name": name, "peerURLs": ["http://{}:2380".format(ip)]}
            cxn = httplib.HTTPConnection(existing, 4000)
            if not replacement:
                cxn.request("POST", "/v2/members", json.dumps(own_data), {"Content-Type": "application/json"})
                cxn.getresponse().read()

            cxn.request("GET", "/v2/members?consistent=false");
            member_data = json.loads(cxn.getresponse().read())
            member_data['members'].append(own_data)
            cluster = ",".join(["{}={}".format(m['name'], m['peerURLs'][0]) for m in member_data['members'] if m['name'] != ""])
            self._subprocess = Popen(shlex.split(subsequent_cmd.format(ip, name, EtcdServer.datadir, cluster)),
                                     #stdout=PIPE,
                                     #stderr=PIPE
                                     )
        sleep(2)
        cxn = httplib.HTTPConnection(ip, 4000)
        cxn.request("GET", "/v2/members");
        member_data = json.loads(cxn.getresponse().read())['members']
        me = filter(lambda x: x['name'] == name, member_data)
        #assert(len(me) == 1)
        self._id = me[0]['id']

    def crash(self):
        self._subprocess.send_signal(SIGTERM)
        self._subprocess.communicate()


    def delete(self, peer):
        cxn = httplib.HTTPConnection(peer, 4000)
        cxn.request("DELETE", "/v2/members/{}".format(self._id));
        cxn.getresponse().read()
        #self._subprocess.send_signal(SIGTERM)

    def client(self):
        return etcd.Client(self._ip, port=4000)
