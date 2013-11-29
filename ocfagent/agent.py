#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import os
import sys

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


class ResourceAgent(object):
	PARAMS=None
	VERSION="0.11"
	__OCF_ENV_MANDATORY=["OCF_ROOT","OCF_RA_VERSION_MAJOR","OCF_RA_VERSION_MINOR","OCF_RESOURCE_PROVIDER","OCF_RESOURCE_INSTANCE","OCF_RESOURCE_TYPE"]
	# Valid OCF Handlers exlucding meta-data and validate-all (implemented in ResourceAgent)

	__OCF_HANDLERS_MANDATORY=["start","stop","monitor"]
	__OCF_HANDLERS_OPTIONAL=["promote","demote","migrate_to","migrate_from","notify","recover","reload"]
	__OCF_VALID_HANDLERS=__OCF_HANDLERS_MANDATORY+__OCF_HANDLERS_OPTIONAL
	__ATTRIBUTES_MANDATORY=["version","longdesc","shortdesc"]

	def __init__(self,unit_test=False):
		self.OCF_ENVIRON = {}
		self.HA_ENVIRON = {}
		self.res_type=None
		self.res_instance=None
		self.res_clone=False
		self.res_clone_id=-1
		self.res_provider=None

		self.name=self.__class__.__name__

		for attr in self.__ATTRIBUTES_MANDATORY:
			if not hasattr(self,attr):
				raise RuntimeError("OCF Agent must have class function %s defined" % attr)

		for attr in self.__OCF_HANDLERS_MANDATORY:
			if not hasattr(self,"handle_%s" % attr):
				raise OCFErrUnimplemented("Mandatory handler %s is not implemented" % attr)

		self.params={}
		
		self.unit_test = unit_test
		
		self.handlers=self.get_implemented_handlers()

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
				print "Found handler",handler
				handler_dict={}
				handler_dict["name"] = handler
				func = getattr(self, "handle_%s" % handler)
				print "argcount",func.func_code.co_argcount,func.func_code.co_varnames,func.func_defaults
				print inspect.getargspec(func)
				handler_dict["timeout"] = 10
				valid_handlers.append(handler_dict)
		return valid_handlers

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
		eResourceAgent = etree.Element("resource-agent", {"name": self.name, "version": self.version()})
		etree.SubElement(eResourceAgent, "version").text = "1.0"
		etree.SubElement(eResourceAgent, "longdesc", {"lang": "en"}).text = self.longdesc()
		etree.SubElement(eResourceAgent, "shortdesc", {"lang": "en"}).text = self.shortdesc()
		eParameters = etree.SubElement(eResourceAgent, "parameters")
		for p in (p.getelement() for p in self.params.values()):
			eParameters.append(p)

		eActions = etree.SubElement(eResourceAgent, "actions")
		for handler in self.handlers:
			p = {}
			p["name"] = handler["name"]
			#p['timeout'] = str(handler.timeout)
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

 	#def handle_start(self,timeout):
	#	raise OCFErrUnimplemented()
	#
 	#def handle_stop(self,timeout):
 	#	raise OCFErrUnimplemented()
	#
 	#def handle_migrate_to(self,timeout,target):
 	#	raise OCFErrUnimplemented()
	#
	#def handle_migrate_from(self,timeout,source):
 	#	raise OCFErrUnimplemented()
	#
	#def handle_promote(self,):
	#	raise OCFErrUnimplemented()
	#
	#def handle_notify_post_start(self,timeout, *nodes):
	#	raise OCFErrUnimplemented()
