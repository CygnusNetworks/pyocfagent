#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import types

from lxml import etree

import error

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
				raise error.OCFErrUnimplemented("Mandatory handler %s is not implemented" % attr)

		self.testmode = testmode

		self.handlers = self.get_implemented_handlers()
		self.parameter_spec = self.get_parameter_spec()
		self.action = None

		if len(sys.argv) > 1:
			if not action in ["meta-data","usage"]:
				self.parse_environment()
				self.parse_parameters()

	def get_action(self):
		if not len(sys.argv) > 1:
			return None
		action = sys.argv[1]
		if not action in self.handlers.keys() + ["meta-data", "usage"]:
			raise RuntimeError("Specified action %s is not a defined handler" % action)
		return action

	def cmdline_call(self):
		action = self.get_action()
		if action is None:
			self.usage()
			raise error.OCFErrUnimplemented("No action specified")
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
				func = getattr(self, "handle_%s" % handler)
				assert func.func_code.co_argcount > 1
				assert func.func_code.co_varnames[0] == "self"
				i = 0
				for var in func.func_code.co_varnames[:func.func_code.co_argcount]:
					if var == "self":
						continue
					handler_dict[var] = func.func_defaults[i]
					i += 1
				if "timeout" not in handler_dict.keys():
					raise RuntimeError("Handler %s does not have parameter timeout" % handler)
				valid_handlers[handler] = handler_dict
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
					raise error.OCFErrArgs("Mandatory environment variable %s not found" % entry)

			ocf_ra_version = "%i.%i" % (int(self.OCF_ENVIRON["OCF_RA_VERSION_MAJOR"]),
										int(self.OCF_ENVIRON["OCF_RA_VERSION_MINOR"]))
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

	def parse_parameters(self):
		if self.testmode == False:
			assert len(self.OCF_ENVIRON)>0
		if self.get_action() in ["meta-data", "usage"]:
			return
		for param_cls in self.parameter_spec:
			cls_name = param_cls.name
			env_name = "%s%s" % (OCF_RESKEY_PREFIX, cls_name)
			if param_cls.type_def == types.IntType:
				param_cls.value = int(self.OCF_ENVIRON[env_name])
			elif param_cls.type_def == types.StringType:
				param_cls.value = str(self.OCF_ENVIRON[env_name])
			elif param_cls.type_def == types.BooleanType:
				param_cls.value = self.OCF_ENVIRON[env_name]

	def get_parameter(self,name):
		found_cls = None
		for param_cls in self.parameter_spec:
			if name == param_cls.name:
				found_cls = param_cls

		assert found_cls != None
		return found_cls.value


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
