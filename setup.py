#!/usr/bin/env python

from setuptools import setup

from os.path import abspath, dirname, join
execfile(join(dirname(abspath(__file__)), 'src', 'PysphereLibrary', 'version.py'))

DESCRIPTION = """
Robot Framework test library for VMWare interaction

The library has the following main usages:
- Identifying available virtual machines on a vCenter or 
  ESXi host
- Starting and stopping VMs
- Shutting down, rebooting VM guest OS
- Checking VM status
- Reverting VMs to a snapshot
- Retrieving basic VM properties
"""[1:-1]

setup(
	name='robotframework-pyspherelibrary',
	version=VERSION,
	description='Robot Framework test library for VMWare Services',
	long_description=DESCRIPTION,
	license='Apache License 2.0',
	keywords='robotframework testing testautomation vmware pysphere',
	platforms='any',
	package_dir={'': 'src'},
	packages=['PysphereLibrary'],
	install_requires=['robotframework','pysphere'])