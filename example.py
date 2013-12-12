#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import types

import ocfagent.agent
import ocfagent.parameter


class TestOCF(ocfagent.agent.ResourceAgent):
	VERSION = "0.10"
	LONGDESC = "This is a TestOCF agent simply for demonstrating functionality"
	SHORTDESC = "Demo OCF agent"


	class OCFParameter_fake(ocfagent.parameter.ResourceStringParameter):
		"""Fake parameter
This is a OCF Ressource fake parameter"""
		@property
		def default(self):
			return "bla"

	def handle_start(self,timeout=1):
		print "handle_start called"

	def handle_stop(self,timeout=10):
		print "handle stop called"

	def handle_monitor(self,timeout=10):
		print "handle monitor called"

if __name__ == "__main__":
	
	ocf=TestOCF()
	ocf.handle_start()
	ocf.meta_data()
