#!/usr/bin/env python

from distutils.core import setup


with open("README.rst") as file:
    long_description = file.read()
with open("LICENSE") as file:
    license = file.read()

setup(name="etcd-py",
        version="0.0.2",
        description="Client for Etcd",
        long_description=long_description,
        author="Kris Foster",
        author_email="kris.foster@gmail.com",
        maintainer="Kris Foster",
        maintainer_email="kris.foster@gmail.com",
        url="https://github.com/transitorykris/etcd-py",
        download_url="",
        classifiers=("Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7"),
        license=license,
        packages=['etcd'],
        )
