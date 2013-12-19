#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Defined exit codes. See: http://www.opencf.org/cgi-bin/viewcvs.cgi/specs/ra/resource-agent-api.txt?rev=HEAD

OCF_SUCCESS = 0
OCF_ERR_GENERIC = 1
OCF_ERR_ARGS = 2
OCF_ERR_UNIMPLEMENTED = 3
OCF_ERR_PERM = 4
OCF_ERR_INSTALLED = 5
OCF_ERR_CONFIGURED = 6
OCF_NOT_RUNNING = 7
OCF_RUNNING_MASTER = 8
OCF_FAILED_MASTER = 9


class ResourceAgentException(SystemExit):
	def __init__(self, error_code, message):
		self.error_code = error_code
		self.message = message
		print "ResourceAgentException:", message, "- exit code", error_code
		SystemExit.__init__(self, error_code)

	def __str__(self):
		return repr(self.message)

# Resource agent exceptions. See: http://www.linux-ha.org/doc/dev-guides/ra-dev-guide.html for usage

class OCFSuccess(ResourceAgentException):
	"""No error, action succeeded completely.
	The action completed successfully. This is the expected return code for any successful start, stop, promote,
	demote, migrate_from, migrate_to, meta_data, help, and usage action.
	For monitor (and its deprecated alias, status), however, a modified convention applies:

	For primitive (stateless) resources, OCF_SUCCESS from monitor means that the resource is running.
	Non-running and gracefully shut-down resources must instead return OCF_NOT_RUNNING.
	For master/slave (stateful) resources, OCF_SUCCESS from monitor means that the resource is running in
	Slave mode. Resources running in Master mode must instead return OCF_RUNNING_MASTER, and gracefully shut-down
	resources must instead return OCF_NOT_RUNNING.
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_SUCCESS, message)

class OCFErrGeneric(ResourceAgentException):
	"""generic or unspecified error (current practice)
	The "monitor" operation shall return this for a crashed, hung or
	otherwise non-functional resource.
	The action returned a generic error. A resource agent should use this exit code only when none of the more
	specific error codes, defined below, accurately describes the problem. The cluster resource manager interprets
	this exit code as a soft error. This means that unless specifically configured otherwise, the resource manager
	will attempt to recover a resource which failed with OCF_ERR_GENERIC in-place — usually by restarting the
	resource on the same node.
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_ERR_GENERIC, message)


class OCFErrArgs(ResourceAgentException):
	"""invalid or excess argument(s)
	Likely error code for validate-all, if the instance parameters
	do not validate. Any other action is free to also return this
	exit status code for this case.
	The resource agent was invoked with incorrect arguments. This is a safety net "can’t happen"
	error which the resource agent should only return when invoked with, for example, an incorrect
	number of command line arguments.
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_ERR_ARGS, message)

class OCFErrUnimplemented(ResourceAgentException):
	"""unimplemented feature (for example, "reload")
	The resource agent was instructed to execute an action that the agent does not implement.
	Not all resource agent actions are mandatory. promote, demote, migrate_to, migrate_from, and notify,
	are all optional actions which the resource agent may or may not implement. When a non-stateful resource agent
	is misconfigured as a master/slave resource, for example, then the resource agent should alert the user about
	this misconfiguration by returning OCF_ERR_UNIMPLEMENTED on the promote and demote actions.
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_ERR_UNIMPLEMENTED, message)

class OCFErrPerm(ResourceAgentException):
	"""user had insufficient privilege
	The action failed due to insufficient permissions. This may be due to the agent not being able to open
	a certain file, to listen on a specific socket, to write to a directory, or similar.
	The cluster resource manager interprets this exit code as a hard error. This means that unless specifically
	configured otherwise, the resource manager will attempt to recover a resource which failed with this error
	by restarting the resource on a different node (where the permission problem may not exist).
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_ERR_PERM, message)

class OCFErrInstalled(ResourceAgentException):
	"""program is not installed
	The action failed because a required component is missing on the node where the action was executed.
	This may be due to a required binary not being executable, or a vital configuration file being unreadable.
	The cluster resource manager interprets this exit code as a hard error. This means that unless specifically
	configured otherwise, the resource manager will attempt to recover a resource which failed with this error by
	restarting the resource on a different node (where the required files or binaries may be present).	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_ERR_INSTALLED, message)

class OCFErrConfigured(ResourceAgentException):
	"""program is not configured
	The action failed because the user misconfigured the resource. For example, the user may have configured an
	alphanumeric string for a parameter that really should be an integer.
	The cluster resource manager interprets this exit code as a fatal error. Since this is a configuration
	error that is present cluster-wide, it would make no sense to recover such a resource on a different node,
	let alone in-place. When a resource fails with this error, the cluster manager will attempt to shut down
	the resource, and wait for administrator intervention.	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_ERR_CONFIGURED, message)

class OCFNotRunning(ResourceAgentException):
	"""program is not running
	Note: This is not the error code to be returned by a successful
	"stop" operation. A successful "stop" operation shall return 0.
	The "monitor" action shall return this value only for a
	_cleanly_ stopped resource. If in doubt, it should return 1.
	The resource was found not to be running. This is an exit code that may be returned by the monitor
	action exclusively. Note that this implies that the resource has either gracefully shut down, or has never
	been started.
	If the resource is not running due to an error condition, the monitor action should instead
	return one of the OCF_ERR_ exit codes or OCF_FAILED_MASTER.	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_NOT_RUNNING, message)

class OCFRunningMaster(ResourceAgentException):
	"""The resource was found to be running in the Master role. This applies only to stateful (Master/Slave)
	resources, and only to their monitor action.
	Note that there is no specific exit code for "running in slave mode". This is because their is no functional
	distinction between a primitive resource running normally, and a stateful resource running as a slave.
	The monitor action of a stateful resource running normally in the Slave role should simply return OCF_SUCCESS.
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_RUNNING_MASTER, message)

class OCFFailedMaster(ResourceAgentException):
	"""The resource was found to have failed in the Master role. This applies only to stateful (Master/Slave)
	resources, and only to their monitor action.
	The cluster resource manager interprets this exit code as a soft error. This means that unless specifically
	configured otherwise, the resource manager will attempt to recover a resource which failed with
	$OCF_FAILED_MASTER in-place — usually by demoting, stopping, starting and then promoting the resource on
	the same node.
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_FAILED_MASTER, message)