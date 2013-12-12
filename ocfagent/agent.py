#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import types

#from xml.etree import ElementTree
from lxml import etree

OCF_SUCCESS=0
OCF_ERR_GENERIC=1
OCF_ERR_ARGS=2
OCF_ERR_UNIMPLEMENTED=3
OCF_ERR_PERM=4
OCF_ERR_INSTALLED=5
OCF_ERR_CONFIGURED=6
OCF_ERR_NOT_RUNNING=7
OCF_ERR_RUNNING_MASTER=8
OCF_FAILED_MASTER=9

class ResourceAgentException(SystemExit):
	def __init__(self,error_code,message):
		self.error_code=error_code
		print "ResourceAgentException:",message
		SystemExit.__init__(self,error_code)
	def __str__(self):
		return repr(self.error_code)

class OCFSuccess(ResourceAgentException):
	def __init__(self,message):
		ResourceAgentException.__init__(self,OCF_SUCCESS,message)

class OCFErrArgs(ResourceAgentException):
	def __init__(self,message):
		ResourceAgentException.__init__(self,OCF_ERR_ARGS,message)
		
class OCFErrUnimplemented(ResourceAgentException):
	def __init__(self,message):
		ResourceAgentException.__init__(self,OCF_ERR_UNIMPLEMENTED,message)


class AttributeVerifier(type):
	"""This metaclass carries out two checks.

	At class construction time it verifies that an attribute
	"ATTRIBUTES_MANDATORY" is present.

	At object construction time it verifies that all elements of the
	"ATTRIBUTES_MANDATORY" attribute are available.
	"""
	instance = None

	def __new__(cls, name, parents, attributes):
		"""Class constructor."""
		newcls = type.__new__(cls, name, parents, attributes)
		if not hasattr(newcls, "ATTRIBUTES_MANDATORY"):
			raise RuntimeError("instances of AttributeVerifier must have an ATTRIBUTES_MANDATORY attribute")
		cls.name=name
		return newcls

	def __call__(cls, *args, **kwargs):
		"""Object constructor."""

		obj = type.__call__(cls, *args, **kwargs)
		for attr in cls.ATTRIBUTES_MANDATORY:
			if not hasattr(cls, attr):
				raise RuntimeError("attribute %r required on class %r" % (attr, cls.name))


		if cls.instance is None:
			cls.instance = super(AttributeVerifier, cls).__call__(*args, **kwargs)

		return cls.instance


class ResourceAgent(object):
	__metaclass__ = AttributeVerifier
	__OCF_ENV_MANDATORY=["OCF_ROOT","OCF_RA_VERSION_MAJOR","OCF_RA_VERSION_MINOR","OCF_RESOURCE_PROVIDER","OCF_RESOURCE_INSTANCE","OCF_RESOURCE_TYPE"]
	# Valid OCF Handlers exlucding meta-data and validate-all (implemented in ResourceAgent)

	__OCF_HANDLERS_MANDATORY=["start","stop","monitor"]
	__OCF_HANDLERS_OPTIONAL=["promote","demote","migrate_to","migrate_from","notify","recover","reload"]
	__OCF_VALID_HANDLERS=__OCF_HANDLERS_MANDATORY+__OCF_HANDLERS_OPTIONAL
	ATTRIBUTES_MANDATORY=["VERSION","LONGDESC","SHORTDESC"]

	def __init__(self,unit_test=False):
		self.OCF_ENVIRON = {}
		self.HA_ENVIRON = {}
		self.res_type=None
		self.res_instance=None
		self.res_clone=False
		self.res_clone_id=-1
		self.res_provider=None

		self.name=self.__class__.__name__

		for attr in self.__OCF_HANDLERS_MANDATORY:
			if not hasattr(self,"handle_%s" % attr):
				raise OCFErrUnimplemented("Mandatory handler %s is not implemented" % attr)
		
		self.unit_test = unit_test
		
		self.handlers=self.get_implemented_handlers()
		self.parameter_spec=self.get_parameter_spec()

		if len(sys.argv)<=1:
			self.usage()
		else:
			self.parse_environment()
	
	def usage(self):
		calls=[handler["name"] for handler in self.handlers]+["usage","meta-data"]
		print "usage: %s {%s}" % (self.name, "|".join(calls))
	
	def get_implemented_handlers(self):
		valid_handlers=[]
		for handler in self.__OCF_VALID_HANDLERS:
			if hasattr(self,"handle_%s" % handler):
				handler_dict={}
				handler_dict["name"] = handler
				func = getattr(self, "handle_%s" % handler)
				assert func.func_code.co_argcount>1
				assert len(func.func_code.co_varnames)==func.func_code.co_argcount
				assert func.func_code.co_varnames[0]=="self"
				#TODO: each parameter is required to have a default. Is this good?
				assert len(func.func_code.co_varnames)-1==len(func.func_defaults)
				i=0
				for var in func.func_code.co_varnames:
					if var=="self":
						continue
					func.func_defaults[i]
					handler_dict[var] = func.func_defaults[i]
					i+=1
				#TODO: add handler parameter validaton?
				if "timeout" not in handler_dict.keys():
					raise RuntimeError("Handler %s does not have parameter timeout" % handler)
				valid_handlers.append(handler_dict)
		return valid_handlers

	def get_parameter_spec(self):
		env = os.environ
		params = []
		for entry in dir(self):
			if entry.startswith("OCFParameter_"):
				name=entry[len("OCFParameter_"):]
				parameter_class=getattr(self,entry)

				param_instance = parameter_class()
				if param_instance.type_def not in [types.IntType,types.StringType,types.BooleanType]:
					raise RuntimeError("type_def property of parameter class is not of known types")

				env_name = "OCF_RESKEY_"+name
				if param_instance.required and not env.has_key(env_name):
					raise RuntimeError("os.environ is missing required parameter %s" % (env_name,))

				if param_instance.shortdesc == None:
					raise RuntimeError("Parameter %s short description is not present" % name)
				if param_instance.longdesc == None:
					raise RuntimeError("Parameter %s long description is not present" % name)

				params.append(param_instance)
		return params


	def parse_environment(self):
		env = os.environ
		
		for key in env.keys():
			if key.startswith("HA_"):
				self.HA_ENVIRON[key]=env[key]
			if key.startswith("OCF_"):
				self.OCF_ENVIRON[key]=env[key]
		
		if not self.unit_test:
			for entry in self.__OCF_ENV_MANDATORY:
				if entry not in self.OCF_ENVIRON.keys():
					raise OCFErrArgs("Mandatory environment variable %s not found" % entry)
		
		#FIXME: Check RA Version Major and Minor. Check Resource provider?
		#FIXME: get clone number
		#FIXME: get ocf resource type
			pos=self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"].find(":")
			if pos>=0:
				self.res_instance=self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"][:pos]
				self.res_clone=True
				self.res_clone_id=int(self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"][pos+1:])
			else:
				self.res_instance=self.OCF_ENVIRON["OCF_RESOURCE_INSTANCE"]
			self.res_type=self.OCF_ENVIRON["OCF_RESOURCE_TYPE"]
			self.res_provider=self.OCF_ENVIRON["OCF_RESOURCE_PROVIDER"]
			

	def meta_data_xml(self):
		eResourceAgent = etree.Element("resource-agent", {"name": self.name, "version": self.VERSION})
		etree.SubElement(eResourceAgent, "version").text = "1.0"
		etree.SubElement(eResourceAgent, "longdesc", {"lang": "en"}).text = self.LONGDESC
		etree.SubElement(eResourceAgent, "shortdesc", {"lang": "en"}).text = self.SHORTDESC
		eParameters = etree.SubElement(eResourceAgent, "parameters")
		for p in self.parameter_spec:
			if p.required:
				required = 1
			else:
				required = 0
			if p.unique:
				unique = 1
			else:
				unique = 0

			eParameter=etree.Element("parameter", { "name": p.name, "unique": str(unique), "required": str(required) })
			etree.SubElement(eParameter, "longdesc", { "lang": "en" }).text = p.longdesc
			etree.SubElement(eParameter, "shortdesc", { "lang": "en" }).text = p.shortdesc
			if p.default is not None:
				content_data = { "type": p.type_name, "default": p.default }
			else:
				content_data = { "type": p.type_name }
			etree.SubElement(eParameter, "content", content_data)
			eParameters.append(eParameter)

		eActions = etree.SubElement(eResourceAgent, "actions")
		for handler in self.handlers:
			p = {}
			for key in handler.keys():
				p[key] = str(handler[key])

			eActions.append(etree.Element("action", p))

		return eResourceAgent

	def meta_data(self):

		xml_data=self.meta_data_xml()
		#text="""<?xml version="1.0"?>
#<!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">
#"""
		#sys.stdout.write(text)
		xml_data.addprevious(etree.PI('xm'))
		print etree.tostring(xml_data, pretty_print=True,xml_declaration=True, encoding='utf-8',doctype="""<!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">""")
		sys.stdout.write("\n")
