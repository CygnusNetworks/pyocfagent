#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ocfagent import __author__, __copyright__, __license__, __version__, __maintainer__, __email__, __status__  # pylint: disable=W0611
import setuptools

setuptools.setup(name="pyocfagent",
	version=__version__,
	author=__author__,
	author_email=__email__,
	description='Python OCF Resource Agent Framework for Pacemaker Clusters',
	long_description="This is a Python OCF Cluster Resource Agent Framework for implementing OCF Resource Agents in Python. It allows you to implement a OCF compatible resource agent for Pacemaker with pure Python logic. Most Resource agents are implemented as Shell Scripts (see Debian Package resource-agents for examples). The pyocfagent allows you to implement such resource agents directly in Python. The framework creates resource agent meta-data on the fly from your source code by introspection of your derived Pyhon class.",
	packages=["ocfagent"],
	license=__license__,
	platforms='POSIX',
	url='https://github.com/CygnusNetworks/pyocfagent',
	download_url='https://github.com/CygnusNetworks/pyocfagent/tarball/v0.12',
	classifiers=[
		"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2.7",
		"Development Status :: 5 - Production/Stable",
		"Operating System :: POSIX",
		"Topic :: Internet",
		"Topic :: System :: Networking",
	],
	keywords=["pacemaker", "ocf", "agent", "python"],
	install_requires=['lxml'],
)
