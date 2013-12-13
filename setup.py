#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ocfagent import __author__, __copyright__, __license__, __version__, __maintainer__, __email__, __status__ # pylint: disable=W0611
from distutils.core import setup

setup(name="ocfagent",
	version = __version__,
	author = __author__,
	author_email = __email__,
	packages = ["ocfagent"],
	license = __license__,
	classifiers = [
		"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
		"Programming Language :: Python",
		"Development Status :: 3 - Alpha",
		"Operating System :: POSIX"
	]
)