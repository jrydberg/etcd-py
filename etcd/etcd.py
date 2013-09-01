"""
A Python client for Etcd

This is a Python client for Etcd.

Etcd can be found at: https://github.com/coreos/etcd

See README.rst for details on how to use this module

Copyright (C) 2013 Kris Foster
See LICENSE for more details
"""

from urlparse import urlparse
from collections import namedtuple

import requests


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4001

KEYS_URL = "{}/v1/keys/{}"
WATCH_URL = "{}/v1/watch/{}"
MACHINES_URL = "{}/v1/machines"
LEADER_URL = "{}/v1/leader"
LIST_URL = "{}/v1/keys/{}/"

EtcdSet = namedtuple("set", "index, newKey, prevValue, expiration")
EtcdGet = namedtuple("get", "index, value")
EtcdDelete = namedtuple("delete", "index, prevValue")
EtcdWatch = namedtuple("watch", "action, value, key, index, newKey")
EtcdTestAndSet = namedtuple("testandset", "index, key, prevValue, expiration")
EtcdList = namedtuple("list", "key, index, value, dir")


class EtcdError(BaseException):
    """Generic etcd error"""
    pass


class Etcd(object):
    """Talks to an etcd instance"""
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, ssl_cert=None,
            ssl_key=None, follow_leader=True, autostart=True):
        """
        host: sets the hostname or IP address of the etcd server
        port: sets the port that the server is listening on
        ssl_cert / ssl_key: specify an optional client certificate and key
        follow_leader: if True we will always try to follow the current leader
            (not yet implemented fully!)
        autostart: start the client from the constructor
        Note: ssl_cert may be set to a file containing both certificate and
            key
        """
        self.requests = requests.Session()
        self.ssl_conf = None
        if ssl_cert and ssl_key:
            # separate cert and key files
            self.ssl_conf = (ssl_cert, ssl_key)
        elif ssl_cert:
            # this should be a pem containing both cert and key
            self.ssl_conf = ssl_cert
        if self.ssl_conf:
            schema = "https"
        else:
            schema = "http"
        self.base_url = "{}://{}:{}".format(schema, host, port)
        self.current_leader = None
        self.follow_leader = follow_leader
        self._machines_cache = None
        if autostart:
            self.start()

    def start(self):
        """Start the client.
        """
        self.current_leader = self.leader()
        if self.follow_leader:
            # not quite right! leader returns the server port not client!
            #self.base_url = self.current_leader
            # not quite right either! schema doesn't follow client's prefered
            # schema
            #self.base_url = self.machines()[0]
            leader_parts = urlparse(self.machines()[0])
            self.base_url = "{}://{}:{}".format(leader_parts.scheme,
                    leader_parts.hostname, leader_parts.port)
        self.machines_cache = None
        self.machines()

    def set(self, key, value, ttl=None):
        """Sets key to value
        
        key: key name to set
        value: value to set the key to
        ttl: optionally specify a time-to-live for this key
        """
        data = {'value': value}
        if ttl:
            data['ttl'] = ttl
        req = self.requests.post(KEYS_URL.format(self.base_url, key), data,
                cert=self.ssl_conf)
        res = req.json()
        if 'newKey' not in res:
            res['newKey'] = False
        if 'prevValue' not in res:
            res['prevValue'] = None
        if 'expiration' not in res:
            res['expiration'] = None
        return EtcdSet(index=res['index'], newKey=res['newKey'],
                prevValue=res['prevValue'], expiration=res['expiration'])

    def get(self, key):
        """Returns the value of the given key
        
        key: the key to retrieve the value for
        """
        req = self.requests.get(KEYS_URL.format(self.base_url, key),
                cert=self.ssl_conf)
        res = req.json()
        if 'errorCode' in res:
            raise EtcdError(res['errorCode'], res['message'])
        return EtcdGet(index=res['index'], value=res['value'])

    def list(self, key):
        """list all the keys under a prefix path.
        
        key: the key to retrieve the value for
        """
        req = self.requests.get(LIST_URL.format(self.base_url, key),
                cert=self.ssl_conf)
        result = req.json()
        if 'errorCode' in result:
            raise EtcdError(res['errorCode'], res['message'])
        for res in result:
            yield EtcdList(key=res['key'][1:], index=res['index'],
                           value=res.get('value'),
                           dir=res.get('dir', False))

    def get_recursive(self, key):
        """Get all keys in a directory."""
        work_queue = [key]
        result = {}
        while work_queue:
            key = work_queue.pop(0)
            for entry in self.list(key):
                if entry.dir:
                    work_queue.append(entry.key)
                else:
                    result[entry.key] = entry.value
        return result

    def delete(self, key):
        """Deletes the given key
        
        key: the key to delete
        """
        req = self.requests.delete(KEYS_URL.format(self.base_url, key),
                cert=self.ssl_conf)
        res = req.json()
        if 'errorCode' in res:
            raise EtcdError(res['errorCode'], res['message'])
        return EtcdDelete(index=res['index'], prevValue=res['prevValue'])

    def watch(self, path, index=None, timeout=None):
        """Watches for changes to key
        
        path: the directory to watch for changes
        index: optionally specify an index value to start at
        timeout: optionally specify a timeout to break out of watch
        """
        try:
            if index:
                req = self.requests.post(WATCH_URL.format(self.base_url, path),
                        {'index': index}, timeout=timeout, cert=self.ssl_conf)
            else:
                req = self.requests.get(WATCH_URL.format(self.base_url, path),
                        timeout=timeout, cert=self.ssl_conf)
        except requests.exceptions.Timeout:
            return None
        res = req.json()
        if 'newKey' not in res:
            res['newKey'] = False
        if 'expiration' not in res:
            res['expiration'] = None
        if 'value' not in res:
            res['value'] = None
        if 'prevValue' not in res:
            res['prevValue'] = None
        return EtcdWatch(action=res['action'], value=res['value'],
                key=res['key'][1:], newKey=res['newKey'], index=res['index'])

    def testandset(self, key, prev_value, value, ttl=None):
        """Atomic test and set
        
        key: the key to test/set
        prev_value: must match the current value of the key
        value: the value to set the key to
        ttl: optionally specify a time-to-live for this key
        """
        data = {'prevValue': prev_value, 'value': value}
        if ttl:
            data['ttl'] = ttl
        req = self.requests.post(KEYS_URL.format(self.base_url, key), data,
                cert=self.ssl_conf)
        res = req.json()
        if 'expiration' not in res:
            res['expiration'] = None
        if 'prevValue' not in res:
            res['prevValue'] = None
        if 'errorCode' in res:
            raise EtcdError(res['errorCode'], res['message'], res['cause'])
        return EtcdTestAndSet(index=res['index'], key=res['key'],
                prevValue=res['prevValue'], expiration=res['expiration'])

    def machines(self):
        """Returns a list of machines in the cluster"""
        req = self.requests.get(MACHINES_URL.format(self.base_url),
                cert=self.ssl_conf)
        self.machines_cache = req.text.split(', ')
        return self.machines_cache

    def leader(self):
        """Returns the leader"""
        req = self.requests.get(LEADER_URL.format(self.base_url),
                cert=self.ssl_conf)
        return req.text
