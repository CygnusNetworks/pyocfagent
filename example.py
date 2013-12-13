#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ocfagent.agent
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


	class OCFParameter_fake(ocfagent.parameter.ResourceStringParameter):
		"""Fake parameter
This is a OCF Ressource fake parameter"""
		@property
		def default(self):
			"""defines the default value for there Resource parameter"""
			return "bla"

	def handle_start(self,timeout=10):
		"""Mandatory Start handler to be implemented"""
		print "handle_start called"

	def handle_stop(self,timeout=10):
		"""Mandatory Stop handler to be implemented"""
		print "handle stop called"

	def handle_monitor(self,timeout=10):
		"""Mandatory monitor handler to be implemented"""
		print "handle monitor called"

	#optional additional handlers
#	def handle_reload(self,timeout = 10):
#		pass

if __name__ == "__main__":
	ocf=TestOCF() # use testmode=True on init to allow calls without environment variables set
	ocf.cmdline_call() # will try to call handle_%s function, specified on cmdline as first argument
