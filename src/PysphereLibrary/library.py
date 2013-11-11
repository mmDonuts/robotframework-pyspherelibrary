from robot.utils import ConnectionCache
from robot.api import logger

from pysphere import VIServer

from .version import VERSION

class PysphereLibrary(object):
    """Robot Framework test library for VMWare interaction

    The library has the following main usages:
    - Identifying available virtual machines on a vCenter or 
      ESXi host
    - Starting and stopping VMs
    - Shutting down, rebooting VM guest OS
    - Checking VM status
    - Reverting VMs to a snapshot
    - Retrieving basic VM properties

    This library is essentially a wrapper around Pysphere
    http://code.google.com/p/pysphere/ adding connection 
    caching consistent with other Robot Framework libraries.
    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = VERSION

    def __init__(self):
        """
        """
        self._connections = ConnectionCache()

    def open_pysphere_connection(self, host, user, password, alias=None):
        """Opens a pysphere connection to the given `host`
        using the supplied `user` and `password`.

        The new connection is made active and any existing connectiosn
        are left open in the background.

        This keyword returns the index of the new connection which
        can be used later to switch back to it. Indices start from `1`
        and are reset when `Close All Pysphere Connections` is called.

        An optional `alias` can be supplied for the connection and used
        for switching between connections. See `Switch Pysphere 
        Connection` for details.

        Example:
        | ${index}= | Open Pysphere Connection | my.vcenter.server.com | username | password | alias=myserver |
        """
        server = VIServer()
        server.connect(host, user, password)
        connection_index = self._connections.register(server, alias)
        logger.info("Pysphere connection opened to host %s" % host)
        return connection_index

    def is_connected_to_pysphere(self):
        return self._connections.current.is_connected()

    def switch_pysphere_connection(self, index_or_alias):
        """Switches the active connection by index of alias.

        `index_or_alias` is either a connection index (an integer)
        or alias (a string). Index can be obtained by capturing
        the return value from `Open Pysphere Connection` and
        alias can be set as a named variable with the same method.

        Example:
        | ${my_connection}= | Open Pysphere Connection | myhost | myuser | mypassword |
        | Open Pysphere Connection | myotherhost | myuser | mypassword | alias=otherhost |
        | Switch Pysphere Connection | ${my_connection} |
        | Power On Vm | myvm |
        | Switch Pysphere Connection | otherhost | 
        | Power On Vm | myothervm |
        """
        old_index = self._connections.current_index
        if index_or_alias is not None:
            self._connections.switch(index_or_alias)
            logger.info("Pysphere connection switched to %s" % index_or_alias)
        else:
            logger.info("No index or alias given, pysphere connection has not been switched.")

    def close_pysphere_connection(self):
        """Closes the current pysphere connection.

        No other connection is made active by this keyword. use
        `Switch Pysphere Connection` to switch to another connection.

        Example:
        | ${my_connection}= | Open Pysphere Connection | myhost | myuser | mypassword |
        | Power On Vm | myvm |
        | Close Pysphere Connection |

        """
        self._connections.current.disconnect()
        logger.info("Connection closed, there will no longer be a current pysphere connection.")
        self._connections.current = self._connections._no_current

    def close_all_pysphere_connections(self):
        """Closes all active pysphere connections.

        This keyword is appropriate for use in test or suite
        teardown. The assignment of connection indices resets
        after calling this keyword, and the next connection
        opened will be allocated index `1`.

        Example:
        | ${my_connection}= | Open Pysphere Connection | myhost | myuser | mypassword |
        | Open Pysphere Connection | myotherhost | myuser | mypassword | alias=otherhost |
        | Switch Pysphere Connection | ${myserver} |
        | Power On Vm | myvm |
        | Switch Pysphere Connection | otherhost | 
        | Power On Vm | myothervm |
        | [Teardown] | Close All Pysphere Connections | 
        """
        self._connections.close_all(closer_method='disconnect')
        logger.info("All pysphere connections closed.")

    def get_vm_names(self):
        """Returns a list of all registered VMs for the
        currently active connection.
        """
        return self._connections.current.get_registered_vms()

    def get_vm_properties(self, name):
        """Returns a dictionary of the properties 
        associated with the named VM.
        """
        vm = self._get_vm(name)
        return vm.get_properties(from_cache=False)

    def power_on_vm(self, name):
        """Power on the vm if it is not
        already running. This method blocks
        until the operation is completed.
        """
        if not self.vm_is_powered_on(name):
            vm = self._get_vm(name)
            vm.power_on()
            logger.info("VM %s powered on." % name)
        else:
            logger.info("VM %s was already powered on." % name)



    def power_off_vm(self, name):
        """Power off the vm if it is not
        already powered off. This method blocks 
        until the operation is completed.
        """        
        if not self.vm_is_powered_off(name):
            vm = self._get_vm(name)
            vm.power_off()   
            logger.info("VM %s was powered off." % name)
        else:
            logger.info("VM %s was already powered off." % name)
        
    def reset_vm(self, name):
        """Perform a reset on the VM. This 
        method blocks until the operation is
        completed.
        """
        vm = self._get_vm(name)
        vm.reset()
        logger.info("VM %s reset." % name)

    def shutdown_vm_os(self, name):
        """Initiate a shutdown in the guest OS 
        in the VM, returning immediately. 
        """
        vm = self._get_vm(name)
        vm.shutdown_guest()
        logger.info("VM %s shutdown initiated." % name)

    def reboot_vm_os(self, name):
        """Initiate a reboot in the guest OS 
        in the VM, returning immediately. 
        """
        vm = self._get_vm(name)
        vm.reboot_guest()
        logger.info("VM %s reboot initiated." % name)

    def vm_is_powered_on(self, name):
        """Returns true if the VM is in the 
        powered on state.
        """
        vm = self._get_vm(name)
        return vm.is_powered_on()          

    def vm_is_powered_off(self, name):
        """Returns true if the VM is in the 
        powered off state.
        """
        vm = self._get_vm(name)
        return vm.is_powered_off()         

    def revert_vm_to_snapshot(self, name, snapshot_name=None):
        """Revert the named VM to a snapshot. If `snapshot_name`
        is supplied it is reverted to that snapshot, otherwise
        it is reverted to the current snapshot. This method
        blocks until the operation is completed.
        """
        vm = self._get_vm(name)
        if snapshot_name is None:
            vm.revert_to_snapshot()
            logger.info("VM %s reverted to current snapshot." % name)
        else:
            vm.revert_to_named_snapshot(snapshot_name)
            logger.info("VM %s reverted to snapshot %s." % name, snapshot_name)

    def _get_vm(self, name):
        connection = self._connections.current
        return connection.get_vm_by_name(name)    



