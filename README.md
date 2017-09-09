[![Build Status](https://travis-ci.org/CygnusNetworks/pyocfagent.svg?branch=master)](https://travis-ci.org/CygnusNetworks/pyocfagent) 
[![Latest Version](https://img.shields.io/pypi/v/pyocfagent.svg)](https://pypi.python.org/pypi/pyocfagent) [![Downloads](https://img.shields.io/pypi/dm/pyocfagent.svg)](https://pypi.python.org/pypi/pyocfagent) [![Downloads PyPi](https://img.shields.io/pypi/dw/pyocfagent.svg)](https://pypi.python.org/pypi/pyocfagent)
[![PyPi Status](https://img.shields.io/pypi/status/pyocfagent.svg)](https://pypi.python.org/pypi/pyocfagent) [![PyPi Versions](https://img.shields.io/pypi/pyversions/pyocfagent.svg)](https://pypi.python.org/pypi/pyocfagent)

pyocfagent
==========

Python OCF Resource Agent Framework for Pacemaker http://clusterlabs.org Clusters

This is a Python OCF Cluster Resource Agent Framework for implementing OCF Resource Agents in Python. It allows you to implement a OCF compatible resource agent for Pacemaker with pure Python logic. Most Resource agents are implemented as Shell Scripts (see Debian Package resource-agents for examples).

The pyocfagent allows you to implement such resource agents directly in Python. The framework creates resource agent meta-data on the fly from your source code by introspection of your derived Pyhon class.

Installing
==========

Clone the git Repository and execute:

python setup.py install

A debian subdir for generating Debian packages is included. If you want to generate a debian package, run:

dpkg-buildpackage

Usage
=====

See provided example.py for a detailed example. For testing purposes you can set testmode=True on constructor. This relaxes environment checking for mandatory environment variables. Only OCF_RESKEY_variable= and OCF_RESOURCE_INSTANCE must be present in the enviroment variables. Use this on development for testing actions without a running pacemaker/corosync framework.

Short example:

<pre>
<code>
#!/usr/bin/env python

import ocfagent.agent
import ocfagent.error
import ocfagent.parameter

class TestOCF(ocfagent.agent.ResourceAgent):
        """Test OCF agent
        """
        VERSION = "0.11"
        """Version of your agent"""
        SHORTDESC = "Demo OCF agent"
        """Short description of your agent for xml meta-data"""
        LONGDESC = "This is a TestOCF agent simply for demonstrating functionality"
        """Long description of your agent for xml meta-data"""
        
        class OCFParameter_test1(ocfagent.parameter.ResourceStringParameter):
                """test1 parameter
This is a OCF Ressource test parameter with string type"""
                @property
                def default(self):
                        return "bla"
                        
        def handle_start(self,timeout=10): # pylint: disable=W0613
                """Mandatory Start handler to be implemented"""
                pass
                
        def handle_stop(self,timeout=10): # pylint: disable=W0613
                """Mandatory Stop handler to be implemented"""
                pass
                
        def handle_monitor(self,timeout=10): # pylint: disable=W0613
                """Mandatory monitor handler to be implemented"""
                pass

if __name__ == "__main__":
        ocf=TestOCF(testmode=False)  # set to True, to enable script testing
        ocf.cmdline_call()
</code>
</pre>
