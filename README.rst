Pysphere Library for Robot Framework
====================================

Introduction
------------

Robot Framework (http://robotframework.org)
test library for VMWare interaction using the
great pysphere library (http://code.google.com/p/pysphere/)

The library has the following main usages:

* Identifying available virtual machines on a vCenter or
  ESXi host
* Starting and stopping VMs
* Shutting down, rebooting VM guest OS
* Checking VM status
* Waiting for VM tools to start running
* Reverting VMs to a snapshot
* Retrieving basic VM properties
* File upload, deletion and relocation
* Directory creation, deletion and relocation

Installation
------------
This package is not yet indexed, but you can install
the tgz or zip file from the local filesystem:

    $ pip install robotframework-pysphere[version-and-filetype]

Or extract the archive and run from the command line:

    $ python setup.py install


License
-------
Copyright 2013, David Weinrich
Copyright 2014, Andy Piper

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
