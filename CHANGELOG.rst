1.0.0
=====
2013-11-10

Initial commit

Features
--------
* List available VMs on a Host
* Power On, Power Off, and Reset a VM by name
* Shutdown, reboot a guest OS by VM name
* Check basic VM status
* Revert a VM to a named or last snapshot
* Capture basic VM properties


1.0.1
=====
2014-03-30

New features
------------
* Wait for VMware tools to start on a VM
* Login to a running VM
* File upload, download, deletion and relocation
* Create, delete and move directories on a VM
* Run processes on a VM synchronously or asynchronously

Bugs fixed
----------
* Fix comparing unicode and non-unicode strings when searching for a VM by name


1.0.2
=====
2014-10-13

Bugs fixed
----------
* When closing a vSphere connection, clear the related VMs from the VM cache
