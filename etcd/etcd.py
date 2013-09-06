"""
A Python client for Etcd

This is a Python client for Etcd.

Etcd can be found at: https://github.com/coreos/etcd

See README.rst for details on how to use this module

Copyright (C) 2013 Kris Foster
See LICENSE for more details
"""

from collections import namedtuple

import requests


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4001


EtcdSet = namedtuple("set", "index, newKey, prevValue, expiration")
EtcdGet = namedtuple("get", "index, value")
EtcdDelete = namedtuple("delete", "index, prevValue")
EtcdWatch = namedtuple("watch", "action, value, key, index, newKey")
EtcdTestAndSet = namedtuple("testandset", "index, key, prevValue, expiration")

KEYS_URL = "{}/v1/keys/{}"
WATCH_URL = "{}/v1/watch/{}"
MACHINES_URL = "{}/v1/machines"
LEADER_URL = "{}/v1/leader"


class EtcdError(BaseException):
    """Generic etcd error"""
    pass


class Etcd(object):
    """Talks to an etcd instance"""
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, ssl_cert=None,
            ssl_key=None):
        """
        host: sets the hostname or IP address of the etcd server
        port: sets the port that the server is listening on
        ssl_cert / ssl_key: specify an optional client certificate and key
        Note: ssl_cert may be set to a file containing both certificate and
        key
        """
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
        self.machine_cache = self.machines()
        self.current_leader = self.leader()

    def set(self, key, value, ttl=None):
        """Sets key to value
        
        key: key name to set
        value: value to set the key to
        ttl: optionally specify a time-to-live for this key
        """
        data = {'value': value}
        if ttl:
            data['ttl'] = ttl
        req = requests.post(KEYS_URL.format(self.base_url, key), data,
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
        req = requests.get(KEYS_URL.format(self.base_url, key),
                cert=self.ssl_conf)
        res = req.json()
        if 'errorCode' in res:
            raise EtcdError(res['errorCode'], res['message'])
        return EtcdGet(index=res['index'], value=res['value'])

    def delete(self, key):
        """Deletes the given key
        
        key: the key to delete
        """
        req = requests.delete(KEYS_URL.format(self.base_url, key),
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
                req = requests.post(WATCH_URL.format(self.base_url, path),
                        {'index': index}, timeout=timeout, cert=self.ssl_conf)
            else:
                req = requests.get(WATCH_URL.format(self.base_url, path),
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
                key=res['key'], newKey=res['newKey'], index=res['index'])

    def testandset(self, key, prev_value, value):
        """Atomic test and set
        
        key: the key to test/set
        prev_value: must match the current value of the key
        value: the value to set the key to
        """
        data = {'prevValue': prev_value, 'value': value}
        req = requests.post(KEYS_URL.format(self.base_url, key), data,
                cert=self.ssl_conf)
        res = req.json()
        if 'expiration' not in res:
            res['expiration'] = None
        if 'errorCode' in res:
            raise EtcdError(res['errorCode'], res['message'], res['cause'])
        return EtcdTestAndSet(index=res['index'], key=res['key'],
                prevValue=res['prevValue'], expiration=res['expiration'])

    def machines(self):
        """Returns a list of machines in the cluster"""
        req = requests.get(MACHINES_URL.format(self.base_url),
                cert=self.ssl_conf)
        return req.text.split(', ')

    def leader(self):
        """Returns the leader"""
        req = requests.get(LEADER_URL.format(self.base_url),
                cert=self.ssl_conf)
        return req.text
