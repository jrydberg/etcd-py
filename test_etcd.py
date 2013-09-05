#!/usr/bin/env python
"""
Test suite for etcd-py
"""

import sys

from etcd import *


if __name__ == '__main__':
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "127.0.0.1"
    e = Etcd(host)
    print e.set("message", "hello world")
    print e.set("message", "Hello World!")
    print e.get("message")
    try:
        print e.get("nonexist")
    except EtcdError as err:
        print err
    print e.delete("message")
    try:
        print e.delete("nonexist")
    except EtcdError as err:
        print err
    print e.set("message", "HELLO WORLD!!", 5)
    print e.watch("foo", timeout=2)
    print e.watch("message")
    e.set("message", "Goodbye, World")
    print e.testandset("message", "Goodbye, World", "Hey Wait!")
    try:
        e.testandset("message", "Goodbye, World", "Try it again")
    except EtcdError as err:
        print err
    print e.machines()
    print e.leader()
