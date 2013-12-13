#!/usr/bin/env python
# -*- coding: utf-8 -*-

import types


class ResourceBaseParameter(object):
	__CLASS_NAME_PREFIX = "OCFParameter_"

	def __init__(self):
		self._value = None
		if not self.__class__.__name__.startswith(self.__CLASS_NAME_PREFIX):
			raise RuntimeError("ResourceParameter class name does not start with %s" % self.__CLASS_NAME_PREFIX)

	@property
	def shortdesc(self):
		if self.__doc__ != None:
			return self.__doc__.split("\n")[0]
		else:
			return None

	@property
	def longdesc(self):
		lines = self.__doc__.split("\n")
		if len(lines) > 1:
			return "\n".join(lines[1:])
		else:
			return None

	@property
	def name(self):
		return self.__class__.__name__[len(self.__CLASS_NAME_PREFIX):]

	@property
	def type_def(self):
		return None

	@property
	def type_name(self):
		if self.type_def == types.IntType:
			return "integer"
		if self.type_def == types.StringType:
			return "string"
		if self.type_def == types.BooleanType:
			return "boolean"


	@property
	def default(self):
		return None

	@property
	def unique(self):
		return True

	@property
	def required(self):
		return False

	@property
	def value(self):
		if self._value == None:
			self.validate_type(self.default)
			return self.default
		else:
			self.validate_type(self._value)
			return self._value

	@value.setter
	def value(self, value):
		self.validate_type(value)
		self._value = value

	def validate_type(self, value=None):
		if value == None:
			value = self._value
		if type(value) != self.type_def:
			raise RuntimeError("Type of value %r is not the same type as Resource Parameter type definition %r" % (
			self._value, self.type_def))


class ResourceStringParameter(ResourceBaseParameter):
	@property
	def type_def(self):
		return types.StringType


class ResourceIntParameter(ResourceBaseParameter):
	@property
	def type_def(self):
		return types.IntType


class ResourceBoolParameter(ResourceBaseParameter):
	_true = frozenset(("1", "t", "true", "yes", "t", True, 1))
	_false = frozenset(("0", "f", "false", "no", "n", False, 0))

	@property
	def type_def(self):
		return types.BooleanType

	def value(self, value):
		if value in self._true:
			self._value = True
			return
		if value in self._false:
			self._value = False
			return
		raise ValueError("Invalid boolean literal: %s" % value)