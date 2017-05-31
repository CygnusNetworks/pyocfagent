#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import types

from lxml import etree

# TODO: monitor OCF_CHECK_LEVEL not yet implemented

from . import error

OCF_RESKEY_PREFIX = "OCF_RESKEY_"


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
		for attr in cls.ATTRIBUTES_MANDATORY:
			if not hasattr(cls, attr):
				raise RuntimeError("attribute %r required on class %r" % (attr, cls.name))
		if cls.instance is None:
			cls.instance = super(AttributeVerifier, cls).__call__(*args, **kwargs)

		return cls.instance


class ResourceAgent(object):  # pylint: disable=R0902
	"""Resource Agent class. Derive agent from this class"""
	__metaclass__ = AttributeVerifier
	"""meta class to validate attributes"""
	__OCF_ENV_MANDATORY = ["OCF_ROOT", "OCF_RA_VERSION_MAJOR", "OCF_RA_VERSION_MINOR", "OCF_RESOURCE_INSTANCE", "OCF_RESOURCE_TYPE"]
	"""Mandatory environment variables to be defined on call
	excluding meta-data and validate-all (implemented in ResourceAgent)"""

	__OCF_HANDLERS_MANDATORY = ["start", "stop", "monitor"]
	"""Mandatory handlers to be implemented"""
	__OCF_HANDLERS_OPTIONAL = ["promote", "demote", "migrate_to", "migrate_from", "notify", "recover", "reload"]
	"""Optional handler to be implemented"""
	__OCF_VALID_HANDLERS = __OCF_HANDLERS_MANDATORY + __OCF_HANDLERS_OPTIONAL
	"""all handlers to be implemented"""
	ATTRIBUTES_MANDATORY = ["VERSION", "LONGDESC", "SHORTDESC"]
	"""Attributes of class to be define in derived classes"""

	def __init__(self, testmode=False):
		self.OCF_ENVIRON = {}
		self.HA_ENVIRON = {}
		self.testmode = testmode
		self.res_type = None
		self.res_instance = None
		self.res_clone = False
		self.res_clone_id = -1
		self.res_provider = None

		self.name = self.__class__.__name__

		# Check if mandatory handlers are implemented
		for attr in self.__OCF_HANDLERS_MANDATORY:
			if not hasattr(self, "handle_%s" % attr):
				raise error.OCFErrUnimplemented("Mandatory handler %s is not implemented" % attr)

		# Get all handlers
		self.handlers = self.get_implemented_handlers()

		# Get action (first cmd line parameter)
		action = self.get_action()

		# Special actions which do not need all environment and parameter specs or variables
		# Allow call without it to help developers implementing
		if action in ["usage", "meta-data"]:
			self.parameter_spec = self.get_parameter_spec(check_env=False)
		else:
			# real call of a handler. Parse environment and parameters
			self.parameter_spec = self.get_parameter_spec(check_env=not self.testmode)
			self.parse_environment()
			self.parse_parameters()

	def get_action(self):
		# if no cmdline parameter is given, call action is usage
		if len(sys.argv) <= 1:
			return "usage"
		# check if the action is a valid implemented handler
		action = sys.argv[1]
		if action not in self.handlers.keys() + ["meta-data", "usage"]:
			raise RuntimeError("Specified action %s is not a defined handler" % action)
		return action

	def cmdline_call(self):
		"""main function, which should be called. Expects cmd line argument and a implemented action"""
		action = self.get_action()
		# Output usage, if action is usage (or none is given)
		if action == "usage":
			self.usage()
			raise error.OCFErrUnimplemented("No action specified")
		# Output xml meta-data
		if action == "meta-data":
			self.meta_data()
		else:
			# Otherwise call implemented handler
			handler = getattr(self, "handle_%s" % action)
			handler()

	def usage(self):
		"""Output usage to stdout listing all implemented handlers"""
		calls = self.handlers.keys() + ["usage", "meta-data"]
		print ("usage: %s {%s}" % (self.name, "|".join(calls)))

	def get_implemented_handlers(self):
		"""get all implemented handlers by searching handle_* functions in class"""
		valid_handlers = {}
		for handler in self.__OCF_VALID_HANDLERS:
			if hasattr(self, "handle_%s" % handler):
				handler_dict = {}
				func = getattr(self, "handle_%s" % handler)
				assert func.func_code.co_argcount > 1
				assert func.func_code.co_varnames[0] == "self"
				# get all handler arguments
				i = 0
				for var in func.func_code.co_varnames[:func.func_code.co_argcount]:
					if var == "self":
						continue
					handler_dict[var] = func.func_defaults[i]
					i += 1
				# Excpect timeout to be always implemented. This is a should in
				# http://www.linux-ha.org/doc/dev-guides/_metadata.html
				# but we will force this here to be present
				if "timeout" not in handler_dict.keys():
					raise RuntimeError("Handler %s does not have parameter timeout" % handler)
				valid_handlers[handler] = handler_dict
		return valid_handlers

	def get_parameter_spec(self, check_env=True):
		"""Get parameter specification from OCFParameter_* classes"""
		env = os.environ
		params = []
		for entry in dir(self):
			if entry.startswith("OCFParameter_"):
				name = entry[len("OCFParameter_"):]
				parameter_class = getattr(self, entry)

				param_instance = parameter_class()
				if param_instance.type_def not in [types.IntType, types.StringType, types.BooleanType]:
					raise RuntimeError("type_def property of parameter class is not of known types")

				# Do not check environment, if check_env is False (usage and meta-data calls)
				if check_env:
					env_name = "OCF_RESKEY_" + name
					if param_instance.required and env_name not in env:
						raise RuntimeError("os.environ is missing required parameter %s" % (env_name,))
				# Extract descriptions
				if param_instance.shortdesc is None:
					raise RuntimeError("Parameter %s short description is not present" % name)
				if param_instance.longdesc is None:
					raise RuntimeError("Parameter %s long description is not present" % name)

				params.append(param_instance)
		return params

	@property
	def is_clone(self):
		"""Check if this is a clone resource"""
		return self.res_clone

	@property
	def clone_id(self):
		"""Return the clone id for cloned resources"""
		return self.res_clone_id

	def parse_environment(self):
		"""Parse environment for HA and OCF environment variables"""
		env = os.environ
		# on a meta-data or usage call return
		if self.get_action() in ["meta-data", "usage"]:
			return
		for key in env.keys():
			if key.startswith("HA_"):
				self.HA_ENVIRON[key] = env[key]
			if key.startswith("OCF_"):
				self.OCF_ENVIRON[key] = env[key]

		if self.testmode:
			ocf_ra_version = "1.0"
		else:
			for entry in self.__OCF_ENV_MANDATORY:
				if entry not in self.OCF_ENVIRON.keys():
					raise error.OCFErrArgs("Mandatory environment variable %s not found" % entry)

			# Excpect a OCF RA Version 1.0 here
			ocf_ra_version = "%i.%i" % (int(self.OCF_ENVIRON["OCF_RA_VERSION_MAJOR"]), int(self.OCF_ENVIRON["OCF_RA_VERSION_MINOR"]))
			assert ocf_ra_version == "1.0"

		# Check if this is a clone
		if "OCF_RESOURCE_INSTANCE" in self.OCF_ENVIRON:
			pos = self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"].find(":")
			if pos >= 0:
				self.res_instance = self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"][:pos]
				self.res_clone = True
				self.res_clone_id = int(self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"][pos + 1:])
			else:
				self.res_instance = self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"]

		if self.testmode is False:
			if "OCF_RESOURCE_TYPE" in self.OCF_ENVIRON:
				self.res_type = self.OCF_ENVIRON["OCF_RESOURCE_TYPE"]
			if "OCF_RESOURCE_PROVIDER" in self.OCF_ENVIRON:
				self.res_provider = self.OCF_ENVIRON["OCF_RESOURCE_PROVIDER"]

	def parse_parameters(self):
		"""Parse parameters (given with OCF_RESKEY_ prefix)"""
		assert len(self.OCF_ENVIRON) > 0
		for param_cls in self.parameter_spec:
			cls_name = param_cls.name
			env_name = "%s%s" % (OCF_RESKEY_PREFIX, cls_name)
			if param_cls.type_def == types.IntType:  # nopep8
				param_cls.value = int(self.OCF_ENVIRON[env_name])
			elif param_cls.type_def == types.StringType:  # nopep8
				param_cls.value = str(self.OCF_ENVIRON[env_name])
			elif param_cls.type_def == types.BooleanType:  # nopep8
				param_cls.value = self.OCF_ENVIRON[env_name]

	def get_parameter(self, name):
		"""get a specific parameter"""
		found_cls = None
		for param_cls in self.parameter_spec:
			if name == param_cls.name:
				found_cls = param_cls

		assert found_cls is not None
		return found_cls.value

	def meta_data_xml(self):
		"""Generate meta-data in XML format"""
		e_resourceagent = etree.Element("resource-agent", {"name": self.name, "version": self.VERSION})  # pylint: disable=E1101
		etree.SubElement(e_resourceagent, "version").text = "1.0"
		etree.SubElement(e_resourceagent, "longdesc", {"lang": "en"}).text = self.LONGDESC  # pylint: disable=E1101
		etree.SubElement(e_resourceagent, "shortdesc", {"lang": "en"}).text = self.SHORTDESC  # pylint: disable=E1101
		e_parameters = etree.SubElement(e_resourceagent, "parameters")
		for p in self.parameter_spec:
			e_parameter = etree.Element("parameter", {"name": p.name, "unique": str(int(p.unique)), "required": str(int(p.required))})
			etree.SubElement(e_parameter, "longdesc", {"lang": "en"}).text = p.longdesc
			etree.SubElement(e_parameter, "shortdesc", {"lang": "en"}).text = p.shortdesc
			if p.default is not None:
				content_data = {"type": p.type_name, "default": str(p.default)}
			else:
				content_data = {"type": p.type_name}
			etree.SubElement(e_parameter, "content", content_data)
			e_parameters.append(e_parameter)

		e_actions = etree.SubElement(e_resourceagent, "actions")
		for handler in self.handlers.keys():

			h = {"name": handler}
			for key in self.handlers[handler]:
				h[key] = str(self.handlers[handler][key])

			e_actions.append(etree.Element("action", h))

		return e_resourceagent

	def meta_data(self):
		"""Output meta data to stdout including doctype"""
		xml_data = self.meta_data_xml()
		xml_data.addprevious(etree.PI('xm'))
		print (etree.tostring(xml_data, pretty_print=True, xml_declaration=True, encoding='utf-8', doctype="""<!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">"""))
		sys.stdout.write("\n")
