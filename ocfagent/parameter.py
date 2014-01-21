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
		"""extracts the documentation from class docstring"""
		if self.__doc__ is not None:
			return self.__doc__.split("\n")[0]
		else:
			return None

	@property
	def longdesc(self):
		"""extracts the documentation from class docstring"""
		lines = self.__doc__.split("\n")
		if len(lines) > 1:
			return "\n".join(lines[1:])
		else:
			return None

	@property
	def name(self):
		"""get the name of the resource from class name removing OCFParameter_ prefix"""
		return str(self.__class__.__name__[len(self.__CLASS_NAME_PREFIX):])

	@name.getter
	def name(self):
		"""get the name of the resource from class name removing OCFParameter_ prefix"""
		return str(self.__class__.__name__[len(self.__CLASS_NAME_PREFIX):])

	@property
	@classmethod
	def type_def(cls):
		"""type definition. Return types.* here in subclasses"""
		return types.NoneType

	@property
	def type_name(self):  # pylint: disable=R0201
		"""get the type name for meta-data here from specified type"""
		if self.type_def == types.IntType:
			return "integer"
		if self.type_def == types.StringType:
			return "string"
		if self.type_def == types.BooleanType:
			return "boolean"

	@property
	def default(self):  # pylint: disable=R0201
		"""return default value. None if none is specified"""
		return None

	@property
	def unique(self):  # pylint: disable=R0201
		"""define this parameter as unique. See section 2.4 of OCF Spec
		The meta data allows the RA to flag one or more instance parameters as
'unique'. This is a hint to the RM or higher level configuration tools
that the combination of these parameters must be unique to the given
resource type.
		"""
		return True

	@property
	def required(self):  # pylint: disable=R0201
		"""define this parameter to be required if true"""
		return False

	@property
	def value(self):
		"""returns the parameter value is set. returns default value if not set"""
		if self._value is None:
			self.validate_type(self.default)
			return self.default
		else:
			self.validate_type(self._value)
			return self._value

	@value.setter
	def value(self, value):
		"""setter for the value"""
		self.validate_type(value)
		self._value = value

	def validate_type(self, value=None):
		"""check if type of set value is consistent with type_def"""
		if value is None:
			value = self._value
		if type(value) != self.type_def:
			raise RuntimeError("Type of value %r is not the same type as Resource Parameter type definition %r" % (self._value, self.type_def))


class ResourceStringParameter(ResourceBaseParameter):
	"""Implement string type"""
	@property
	def type_def(self):
		return types.StringType


class ResourceIntParameter(ResourceBaseParameter):
	"""Implement integer type"""
	@property
	def type_def(self):
		return types.IntType


class ResourceBoolParameter(ResourceBaseParameter):
	"""Implement boolean type"""
	_true = frozenset(("1", "t", "true", "yes", "t", True, 1))
	_false = frozenset(("0", "f", "false", "no", "n", False, 0))

	@property
	def type_def(self):
		return types.BooleanType

	@property
	def value(self):
		if self._value is None:
			self.validate_type(self.default)
			return self.default
		else:
			self.validate_type(self._value)
			return self._value

	@value.setter
	def value(self, val):  # pylint: disable=R0201,W0221
		if val in self._true:
			self._value = True
			return
		if val in self._false:
			self._value = False
			return
		raise ValueError("Invalid boolean literal: %s" % val)
