etcd-py
=======

A python client to etcd (https://github.com/coreos/etcd)

This is very early code.

Getting Started
===============

Set, Get, Delete

.. code-block:: pycon

    >>> import etcd
    >>> e = etcd.Etcd()
    >>> e.set("message", "Hello, World!")
    set(index=48, newKey=True, prevValue=None, expiration=None)
    >>> e.get("message")
    get(index=48, value=u'Hello, World!')
    >>> e.delete("message")
    delete(index=49, prevValue=u'Hello, World!')

Setting a key with a TTL of 3 seconds and watching it with an optional timeout of 5 seconds

.. code-block:: pycon

    >>> set("message", "HELLO WORLD!!", 3)
    set(index=35, newKey=True, prevValue=None, expiration=u'2013-09-05T05:57:33.922332303Z')
    >>> print e.watch("message", timeout=5)
    watch(action=u'DELETE', value=None, key=u'/message', index=35, newKey=False)

Test and set

.. code-block:: pycon

    >>> e.testandset("message", "hello world", "goodbye world")
    testandset(index=37, key=u'/message', prevValue=u'hello world', expiration=None)

Servers

.. code-block:: pycon

    >>> e.machines()
    [u'https://127.0.0.1:4001']
    >>> e.leader()
    http://127.0.0.1:7001

Client certificates

.. code-block:: pycon

    >>> e = etcd.Etcd(ssl_cert="mycert.pem")
    or
    >>> e = etcd.Etcd(ssl_cert="my.crt", ssl_key="my.key")

Author
======

etcd-py is developed and maintained by Kris Foster (kris.foster@gmail.com)
