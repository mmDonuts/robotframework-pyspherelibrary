from robot.utils import ConnectionCache
from robot.api import logger

import os.path
import sys
import time

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
    - Waiting for VM tools to start running
    - Reverting VMs to a snapshot
    - Retrieving basic VM properties
    - File upload, deletion and relocation
    - Directory creation, deletion and relocation
    - Process execution and termination

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
        self._vm_cache = {}


    def open_pysphere_connection(self, host, user, password, alias=None):
        """Opens a pysphere connection to the given `host`
        using the supplied `user` and `password`.

        The new connection is made active and any existing connections
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
        logger.info("Pysphere connection opened to host {}".format(host))
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
            logger.info(u"Pysphere connection switched to {}".format(index_or_alias))
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
        cache_copy = self._vm_cache.copy()
        for name, vm in self._vm_cache.iteritems():
            if id(vm._server) == id(self._connections.current):
                del cache_copy[name]
                logger.debug("Removed VM '{}' from cache".format(name))

        self._vm_cache = cache_copy

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
        self._vm_cache = {}
        logger.info("All pysphere connections closed.")


    def get_vm_names(self):
        """Returns a list of all registered VMs for the
        currently active connection.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | @{vm_names}= | Get Vm Names |
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
            logger.info(u"VM {} powered on.".format(name))
        else:
            logger.info(u"VM {} was already powered on.".format(name))


    def power_off_vm(self, name):
        """Power off the vm if it is not
        already powered off. This method blocks
        until the operation is completed.
        """
        if not self.vm_is_powered_off(name):
            vm = self._get_vm(name)
            vm.power_off()
            logger.info(u"VM {} powered off.".format(name))
        else:
            logger.info(u"VM {} was already powered off.".format(name))


    def reset_vm(self, name):
        """Perform a reset on the VM. This
        method blocks until the operation is
        completed.
        """
        vm = self._get_vm(name)
        vm.reset()
        logger.info(u"VM {} reset.".format(name))


    def shutdown_vm_os(self, name):
        """Initiate a shutdown in the guest OS
        in the VM, returning immediately.
        """
        vm = self._get_vm(name)
        vm.shutdown_guest()
        logger.info(u"VM {} shutdown initiated.".format(name))


    def reboot_vm_os(self, name):
        """Initiate a reboot in the guest OS
        in the VM, returning immediately.
        """
        vm = self._get_vm(name)
        vm.reboot_guest()
        logger.info(u"VM {} reboot initiated.".format(name))


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


    def vm_wait_for_tools(self, name, timeout=120):
        """Waits for up to the `timeout` interval for the VM tools to start
        running on the named VM. VMware tools must be running on the VM for the
        `Vm Login In Guest` keyword to succeed.
        """
        vm = self._get_vm(name)
        vm.wait_for_tools(timeout)
        logger.info(u"VM tools are running on {}.".format(name))


    def vm_login_in_guest(self, name, username, password):
        """Logs into the named VM with the specified `username` and `password`.
        The VM must be powered on and the VM tools must be running on the VM,
        which can be verified using the `Vm Wait For Tools` keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Power On Vm | myvm |
        | Vm Wait For Tools | myvm |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        """
        vm = self._get_vm(name)
        vm.login_in_guest(username, password)
        logger.info(u"Logged into VM {}.".format(name))


    def vm_make_directory(self, name, path):
        """Creates a directory with the specified `path` on the named VM. The
        `Vm Login In Guest` keyword must precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | Vm Make Directory | myvm | C:\\some\\directory\\path |
        """
        vm = self._get_vm(name)
        vm.make_directory(path, True)
        logger.info(u"Created directory {} on VM {}.".format(path, name))


    def vm_move_directory(self, name, src_path, dst_path):
        """Moves or renames a directory from `src_path` to `dst_path` on the
        named VM. The `Vm Login In Guest` keyword must precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | Vm Move Directory | myvm | C:\\directory1 | C:\\directory2 |
        """
        vm = self._get_vm(name)
        vm.move_directory(src_path, dst_path)
        logger.info(u"Moved directory {} to {} on VM {}.".format(
            src_path, dst_path, name))


    def vm_delete_directory(self, name, path):
        """Deletes the directory with the given `path` on the named VM,
        including its contents. The `Vm Login In Guest` keyword must precede
        this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | Vm Delete Directory | myvm | C:\\directory |
        """
        vm = self._get_vm(name)
        vm.delete_directory(path, True)
        logger.info(u"Deleted directory {} on VM {}.".format(path, name))


    def vm_get_file(self, name, remote_path, local_path):
        """Downloads a file from the `remote_path` on the named VM to the
        specified `local_path`, overwriting any existing local file. The
        `Vm Login In Guest` keyword must precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | Vm Get File | myvm | C:\\remote\\location.txt | C:\\local\\location.txt |
        """
        vm = self._get_vm(name)
        vm.get_file(remote_path, local_path, True)
        logger.info(u"Downloaded file {} on VM {} to {}.".format(
            remote_path, name, local_path))


    def vm_send_file(self, name, local_path, remote_path):
        """Uploads a file from `local_path` to the specified `remote_path` on
        the named VM, overwriting any existing remote file. The
        `Vm Login In Guest` keyword must precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | Vm Send File | myvm | C:\\local\\location.txt | C:\\remote\\location.txt |
        """
        local_path = os.path.abspath(local_path)
        logger.info(u"Uploading file {} to {} on VM {}.".format(
            local_path, remote_path, name))
        vm = self._get_vm(name)
        vm.send_file(local_path, remote_path, True)
        logger.info(u"Uploaded file {} to {} on VM {}.".format(
            local_path, remote_path, name))


    def vm_move_file(self, name, src_path, dst_path):
        """Moves a remote file on the named VM from `src_path` to `dst_path`,
        overwriting any existing file at the target location. The
        `Vm Login In Guest` keyword must precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | Vm Move File | myvm | C:\\original_location.txt | C:\\new_location.txt |
        """
        vm = self._get_vm(name)
        vm.move_file(src_path, dst_path, True)
        logger.info(u"Moved file from {} to {} on VM {}.".format(
            src_path, dst_path, name))


    def vm_delete_file(self, name, remote_path):
        """Deletes the file with the given `remote_path` on the named VM. The
        `Vm Login In Guest` keyword must precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | Vm Delete File | myvm | C:\\remote_file.txt |
        """
        vm = self._get_vm(name)
        vm.delete_file(remote_path)
        logger.info(u"Deleted file {} from VM {}.".format(remote_path, name))


    def vm_start_process(self, name, cwd, program_path, *args, **kwargs):
        """Starts a program in the named VM with the working directory specified
        by `cwd`. Returns the process PID. The `Vm Login In Guest` keyword must
        precede this keyword.

        The optional `env` argument can be used to provide a dictionary
        containing environment variables to be set for the program
        being run.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | ${pid}= | Vm Start Process | myvm | C:\\ | C:\\windows\\system32\\cmd.exe | /c | echo | hello world |
        """
        env = kwargs.get('env', None)
        logger.info(u"Starting process '{} {}' on VM {} cwd={} env={}".format(
            program_path, " ".join(args), name, cwd, env))
        vm = self._get_vm(name)
        pid = vm.start_process(program_path, args, env, cwd)
        logger.info(u"Process '{} {}' running on VM {} with pid={} cwd={} env={}".format(
            program_path, " ".join(args), name, pid, cwd, env))
        return pid


    def vm_run_synchronous_process(self, name, cwd, program_path, *args, **kwargs):
        """Executes a process on the named VM and blocks until the process has
        completed. Parameters are the same as for `vm_start_process`. Returns
        the exit code of the process. The `Vm Login In Guest` keyword must
        precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | ${rc}= | Vm Run Synchronous Process | myvm | C:\\ | C:\\windows\\system32\\cmd.exe | /c | echo | hello world |
        | Should Be Equal As Integers | ${rc} | 0 |
        """
        pid = self.vm_start_process(name, cwd, program_path, *args, **kwargs)

        vm = self._get_vm(name)
        while True:
            processes = [x for x in vm.list_processes() if x["pid"] == pid]

            if len(processes) != 1:
                raise Exception("Process terminated and could not retrieve exit code")

            process = processes[0]

            if process['end_time'] != None:
                logger.info(u"Process completed on {}: {}".format(name, repr(process)))
                return process['exit_code']

            time.sleep(2)


    def vm_terminate_process(self, name, pid):
        """Terminates the process with the given `pid` on the named VM. The
        `Vm Login In Guest` keyword must precede this keyword.

        Example:
        | Open Pysphere Connection | myhost | myuser | mypassword |
        | Vm Login In Guest | myvm | vm_username | vm_password |
        | ${pid}= | Vm Start Process | myvm | C:\\ | C:\\windows\\system32\\cmd.exe | /c | pause |
        | Vm Terminate Process | myvm | ${pid} |
        """
        pid = int(pid)
        vm = self._get_vm(name)
        vm.terminate_process(pid)
        logger.info(u"Process with pid {} terminated on VM {}".format(pid, name))


    def revert_vm_to_snapshot(self, name, snapshot_name=None):
        """Revert the named VM to a snapshot. If `snapshot_name`
        is supplied it is reverted to that snapshot, otherwise
        it is reverted to the current snapshot. This method
        blocks until the operation is completed.
        """
        vm = self._get_vm(name)
        if snapshot_name is None:
            vm.revert_to_snapshot()
            logger.info(u"VM {} reverted to current snapshot.".format(name))
        else:
            vm.revert_to_named_snapshot(snapshot_name)
            logger.info(u"VM {} reverted to snapshot {}.".format(
                name, snapshot_name))


    def _get_vm(self, name):
        if name not in self._vm_cache or not self._vm_cache[name]._server.keep_session_alive():
            logger.debug(u"VM {} not in cache or vcenter connection expired.".format(name))
        connection = self._connections.current
        if isinstance(name, unicode):
            name = name.encode("utf8")
            self._vm_cache[name] = connection.get_vm_by_name(name)
        else:
            logger.debug(u"VM {} already in cache.".format(name))

        return self._vm_cache[name]

