etcd-py
=======

A python client to etcd (https://github.com/coreos/etcd)

This is very early code.

Getting Started
===============

.. code-block:: pycon

    >>> import etcd
    >>> e = etcd.Etcd()
    >>> e.set("message", "Hello, World!")
    set(index=192, newKey=False, prevValue=u'Hey Wait!', expiration=None)
    >>> e.get("message")
    get(index=192, value=u'Hello, World!')

Author
======

etcd-py is developed and maintained by Kris Foster (kris.foster@gmail.com)
