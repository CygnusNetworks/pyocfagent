#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import types

from lxml import etree

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
		print "ResourceAgentException:", message, "- exit code", error_code
		SystemExit.__init__(self, error_code)

	def __str__(self):
		return repr(self.error_code)


class OCFSuccess(ResourceAgentException):
	"""No error, action succeeded completely.
	The action completed successfully. This is the expected return code for any successful start, stop, promote, demote, migrate_from, migrate_to, meta_data, help, and usage action.
For monitor (and its deprecated alias, status), however, a modified convention applies:

For primitive (stateless) resources, OCF_SUCCESS from monitor means that the resource is running. Non-running and gracefully shut-down resources must instead return OCF_NOT_RUNNING.
For master/slave (stateful) resources, OCF_SUCCESS from monitor means that the resource is running in Slave mode. Resources running in Master mode must instead return OCF_RUNNING_MASTER, and gracefully shut-down resources must instead return OCF_NOT_RUNNING.
	"""
	def __init__(self, message):
		ResourceAgentException.__init__(self, OCF_SUCCESS, message)

class OCFErrGeneric(ResourceAgentException):
	"""generic or unspecified error (current practice)
	The "monitor" operation shall return this for a crashed, hung or
	otherwise non-functional resource.
	The action returned a generic error. A resource agent should use this exit code only when none of the more specific error codes, defined below, accurately describes the problem.
	The cluster resource manager interprets this exit code as a soft error. This means that unless specifically configured otherwise, the resource manager will attempt to recover a resource which failed with OCF_ERR_GENERIC in-place — usually by restarting the resource on the same node.
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

class AttributeVerifier(type):
	"""This metaclass carries out two checks.

	At class construction time it verifies that an attribute
	"ATTRIBUTES_MANDATORY" is present.

	At object construction time it verifies that all elements of the
	"ATTRIBUTES_MANDATORY" attribute are available.
	"""
	instance = None

	def __new__(mcs, name, parents, attributes):
		"""Class constructor."""
		newcls = type.__new__(mcs, name, parents, attributes)
		if not hasattr(newcls, "ATTRIBUTES_MANDATORY"):
			raise RuntimeError("instances of AttributeVerifier must have an ATTRIBUTES_MANDATORY attribute")
		mcs.name = name
		return newcls

	def __call__(cls, *args, **kwargs):
		"""Object constructor."""

		#obj = type.__call__(cls, *args, **kwargs)
		for attr in cls.ATTRIBUTES_MANDATORY:
			if not hasattr(cls, attr):
				raise RuntimeError("attribute %r required on class %r" % (attr, cls.name))

		if cls.instance is None:
			cls.instance = super(AttributeVerifier, cls).__call__(*args, **kwargs)

		return cls.instance


class ResourceAgent(object):
	__metaclass__ = AttributeVerifier
	__OCF_ENV_MANDATORY = ["OCF_ROOT", "OCF_RA_VERSION_MAJOR", "OCF_RA_VERSION_MINOR", "OCF_RESOURCE_INSTANCE",
						   "OCF_RESOURCE_TYPE"]
	# Valid OCF Handlers exlucding meta-data and validate-all (implemented in ResourceAgent)

	__OCF_HANDLERS_MANDATORY = ["start", "stop", "monitor"]
	__OCF_HANDLERS_OPTIONAL = ["promote", "demote", "migrate_to", "migrate_from", "notify", "recover", "reload"]
	__OCF_VALID_HANDLERS = __OCF_HANDLERS_MANDATORY + __OCF_HANDLERS_OPTIONAL
	ATTRIBUTES_MANDATORY = ["VERSION", "LONGDESC", "SHORTDESC"]

	def __init__(self, testmode=False):
		self.OCF_ENVIRON = {}
		self.HA_ENVIRON = {}
		self.res_type = None
		self.res_instance = None
		self.res_clone = False
		self.res_clone_id = -1
		self.res_provider = None

		self.name = self.__class__.__name__

		for attr in self.__OCF_HANDLERS_MANDATORY:
			if not hasattr(self, "handle_%s" % attr):
				raise OCFErrUnimplemented("Mandatory handler %s is not implemented" % attr)

		self.testmode = testmode

		self.handlers = self.get_implemented_handlers()
		self.parameter_spec = self.get_parameter_spec()
		self.action = None

		if not len(sys.argv) <= 1:
			self.parse_environment()

	def get_action(self):
		if not len(sys.argv) > 1:
			self.usage()
			raise OCFErrUnimplemented("No action specified")
		action = sys.argv[1]
		if not action in self.handlers.keys() + ["meta-data", "usage"]:
			raise RuntimeError("Specified action %s is not a defined handler" % action)
		return action

	def cmdline_call(self):
		action = self.get_action()
		if action == "meta-data":
			self.meta_data()
		elif action == "usage":
			self.usage()
		else:
			self.action = action
			handler = getattr(self, "handle_%s" % action)
			handler()
		#FIXME: if monitor check for OCF_CHECK_LEVEL


	def usage(self):
		calls = self.handlers.keys() + ["usage", "meta-data"]
		print "usage: %s {%s}" % (self.name, "|".join(calls))


	def get_implemented_handlers(self):
		valid_handlers = {}
		for handler in self.__OCF_VALID_HANDLERS:
			if hasattr(self, "handle_%s" % handler):
				handler_dict = {}
				#handler_dict["name"] = handler
				func = getattr(self, "handle_%s" % handler)
				assert func.func_code.co_argcount > 1
				assert len(func.func_code.co_varnames) == func.func_code.co_argcount
				assert func.func_code.co_varnames[0] == "self"
				#TODO: each parameter is required to have a default. Is this good?
				assert len(func.func_code.co_varnames) - 1 == len(func.func_defaults)
				i = 0
				for var in func.func_code.co_varnames:
					if var == "self":
						continue
					handler_dict[var] = func.func_defaults[i]
					i += 1
				#TODO: add handler parameter validaton?
				if "timeout" not in handler_dict.keys():
					raise RuntimeError("Handler %s does not have parameter timeout" % handler)
				valid_handlers[handler] = handler_dict
			#valid_handlers.append(handler_dict)
		return valid_handlers

	def get_parameter_spec(self):
		env = os.environ
		params = []
		for entry in dir(self):
			if entry.startswith("OCFParameter_"):
				name = entry[len("OCFParameter_"):]
				parameter_class = getattr(self, entry)

				param_instance = parameter_class()
				if param_instance.type_def not in [types.IntType, types.StringType, types.BooleanType]:
					raise RuntimeError("type_def property of parameter class is not of known types")

				env_name = "OCF_RESKEY_" + name
				if param_instance.required and not env.has_key(env_name):
					raise RuntimeError("os.environ is missing required parameter %s" % (env_name,))

				if param_instance.shortdesc == None:
					raise RuntimeError("Parameter %s short description is not present" % name)
				if param_instance.longdesc == None:
					raise RuntimeError("Parameter %s long description is not present" % name)

				params.append(param_instance)
		return params

	@property
	def is_clone(self):
		return self.res_clone

	@property
	def clone_id(self):
		return self.res_clone_id

	def parse_environment(self):
		env = os.environ
		# on a meta-data or usage call return
		if self.get_action() in ["meta-data", "usage"]:
			return
		for key in env.keys():
			if key.startswith("HA_"):
				self.HA_ENVIRON[key] = env[key]
			if key.startswith("OCF_"):
				self.OCF_ENVIRON[key] = env[key]

		if not self.testmode:
			for entry in self.__OCF_ENV_MANDATORY:
				if entry not in self.OCF_ENVIRON.keys():
					raise OCFErrArgs("Mandatory environment variable %s not found" % entry)

			ocf_ra_version = "%i.%i" % int(self.OCF_ENVIRON["OCF_RA_VERSION_MAJOR"]), int(
				self.OCF_ENVIRON["OCF_RA_VERSION_MINOR"])
			assert ocf_ra_version == "1.0"
		else:
			ocf_ra_version = "1.0"

		if self.OCF_ENVIRON.has_key("OCF_RESOURCE_INSTANCE"):
			pos = self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"].find(":")
			if pos >= 0:
				self.res_instance = self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"][:pos]
				self.res_clone = True
				self.res_clone_id = int(self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"][pos + 1:])
			else:
				self.res_instance = self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"]

		if self.OCF_ENVIRON.has_key("OCF_RESOURCE_TYPE"):
			self.res_type = self.OCF_ENVIRON["OCF_RESOURCE_TYPE"]
		if self.OCF_ENVIRON.has_key("OCF_RESOURCE_PROVIDER"):
			self.res_provider = self.OCF_ENVIRON["OCF_RESOURCE_PROVIDER"]


	def meta_data_xml(self):
		eResourceAgent = etree.Element("resource-agent", {"name": self.name, "version": self.VERSION}) #pylint: disable=E1101
		etree.SubElement(eResourceAgent, "version").text = "1.0"
		etree.SubElement(eResourceAgent, "longdesc", {"lang": "en"}).text = self.LONGDESC  #pylint: disable=E1101
		etree.SubElement(eResourceAgent, "shortdesc", {"lang": "en"}).text = self.SHORTDESC  #pylint: disable=E1101
		eParameters = etree.SubElement(eResourceAgent, "parameters")
		for p in self.parameter_spec:
			eParameter = etree.Element("parameter",
									   {"name": p.name, "unique": str(int(p.unique)), "required": str(int(p.required))})
			etree.SubElement(eParameter, "longdesc", {"lang": "en"}).text = p.longdesc
			etree.SubElement(eParameter, "shortdesc", {"lang": "en"}).text = p.shortdesc
			if p.default is not None:
				content_data = {"type": p.type_name, "default": p.default}
			else:
				content_data = {"type": p.type_name}
			etree.SubElement(eParameter, "content", content_data)
			eParameters.append(eParameter)

		eActions = etree.SubElement(eResourceAgent, "actions")
		for handler in self.handlers.keys():

			h = {}
			h["name"] = handler
			for key in self.handlers[handler]:
				h[key] = str(self.handlers[handler][key])

			eActions.append(etree.Element("action", h))

		return eResourceAgent

	def meta_data(self):

		xml_data = self.meta_data_xml()
		#text="""<?xml version="1.0"?>
		#<!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">
		#"""
		#sys.stdout.write(text)
		xml_data.addprevious(etree.PI('xm'))
		print etree.tostring(xml_data, pretty_print=True, xml_declaration=True, encoding='utf-8',
							 doctype="""<!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">""")
		sys.stdout.write("\n")
