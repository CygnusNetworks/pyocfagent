#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback

import ocfagent.agent
import ocfagent.error
import ocfagent.parameter

class TestOCF(ocfagent.agent.ResourceAgent):
	"""Test OCF agent
	"""
	VERSION = "0.10"
	"""Version of your agent"""
	SHORTDESC = "Demo OCF agent"
	"""Short description of your agent for xml meta-data"""
	LONGDESC = "This is a TestOCF agent simply for demonstrating functionality"
	"""Long description of your agent for xml meta-data"""

        # Implement parameters. All parameters must be prefixed by OCFParameter_
	class OCFParameter_test1(ocfagent.parameter.ResourceStringParameter):
		"""test1 parameter
This is a OCF Ressource test parameter with string type"""
		@property
		def default(self):
			"""defines the default value for there Resource parameter"""
			return "bla"

	class OCFParameter_test2(ocfagent.parameter.ResourceIntParameter):
		"""test2 parameter
This is a OCF Ressource test parameter with integer type"""
		@property
		def default(self):
			"""defines the default value for there Resource parameter. None if not defined"""
			return 1

		@property
		def required(self):
			"""specifies if parameter is required or not"""
			return True

	class OCFParameter_test3(ocfagent.parameter.ResourceBoolParameter):
		"""test3 parameter
This is a OCF Ressource test parameter with bool type"""
		@property
		def default(self):
			return True

	def handle_start(self,timeout=10): # pylint: disable=W0613
		"""Mandatory Start handler to be implemented"""
		try:
			print "handle_start called with parameters", self.get_parameter("test1"), self.get_parameter("test2")
		except ocfagent.error.ResourceAgentException, msg:
			raise
		except Exception, msg:
			for line in traceback.format_exc(sys.exc_info()[2]).splitlines():
				print "ERROR:", line
			raise ocfagent.error.OCFErrGeneric(msg)

	def handle_stop(self,timeout=10): # pylint: disable=W0613
		"""Mandatory Stop handler to be implemented"""
		try:
			print "handle stop called with parameters", self.get_parameter("test1"), self.get_parameter("test2")
		except ocfagent.error.ResourceAgentException, msg:
			raise
		except Exception, msg:
			for line in traceback.format_exc(sys.exc_info()[2]).splitlines():
				print "ERROR:", line
			raise ocfagent.error.OCFErrGeneric(msg)


	def handle_monitor(self,timeout=10): # pylint: disable=W0613
		"""Mandatory monitor handler to be implemented"""
		try:
			print "handle monitor called with parameters", self.get_parameter("test1"), self.get_parameter("test2")
			# Return on of the following states here. Be sure
			#raise ocfagent.error.OCFSuccess("resource is running")
			#raise ocfagent.error.OCFNotRunning("resource is not running.")
		except ocfagent.error.ResourceAgentException, msg:
			raise
		except Exception, msg:
			for line in traceback.format_exc(sys.exc_info()[2]).splitlines():
				print "ERROR:", line
			raise ocfagent.error.OCFErrGeneric(msg)

	#optional additional handlers
#	def handle_reload(self,timeout = 10):
#		pass

if __name__ == "__main__":
	ocf=TestOCF()
	ocf.cmdline_call() # will try to call handle_%s function, specified on cmdline as first argument
