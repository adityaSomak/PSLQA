from collections import OrderedDict
from numeric import *
from domain import *


class ConstraintTemplate(object):
	"""
	Class for templating constraints of the form:
	similarity(R,R') ==  0.29
	similarity(R,R') >=  0.29
	similarity(R,R') >=  C
	"""
	def __init__(self, function, types, relation, constanttype):
		self.function = function
		self.types = types
		self.relation = relation
		self.constanttype = constanttype


class VariableTypeMap(object):
	def __init__(self):
		self.typeMap = {}

	def addVariable(self, variable, mustExistBefore=False):
		try:
			existingtype =  self.typeMap[variable.name]
			if mustExistBefore or existingtype is not None:
				if variable.type != existingtype:
					raise Exception("Type mismatch for variable:" + variable)
		except KeyError:
			self.typeMap[variable.name] = variable.type


class PredicateTemplateMap(object):
	def __init__(self):
		self.pTemplateMap = {}

	def addTemplate(self, pTemplateName, types):
		try:
			existingtypes = self.pTemplateMap[pTemplateName]
			if existingtypes is not None and existingtypes != types:
				raise Exception("Same predicate with different template cannot exist:" + pTemplateName)
		except KeyError:
			self.pTemplateMap[pTemplateName] = types

class Constant(object):
	def __init__(self, name, type, value):
		self.name = name
		self.type = type
		self.value = value

class Variable(object):

	def __init__(self, name, type, value=None):
		self.name = name
		self.type = type
		if type == ArgumentType.NUMERIC and value is not None:
			domain = Domain(type)
			domain.addElement(value)
			self.domain= domain

	def setDomain(self, domain):
		self.domain = domain

	def __str__(self):
		return "[name="+self.name+", type="+self.type


class ExpressionVariable(object):
	def __init__(self, name, dependentVariables, expression):
		self.name = name
		self.type = ArgumentType.NUMERIC
		self.dependentVariables = sorted(dependentVariables, key=lambda var:len(var.name),reverse=True)
		self.nsp = NumericStringParser()

	def getValue(self, varToValues):
		numString = self.expression
		for var in self.dependentVariables:
			numString.replace(var.name,varToValues[var.name])
		return self.nsp.eval(numString)


class PredicateConstantTemplate(object):

	def __init__(self, name, type, value):
		self.name = name
		self.arity =  0
		self.type = type
		self.value = value


class PredicateTemplate(object):
	"""
	Class for templating Predicates:
	     friends(A,B)
	Example Usage::
	>> friendsT = PredicateTemplate('friends', [ArgumentType.STRING, ArgumentType.String]);
	"""
	def __init__(self, name, types, isEvidence):
		self.name = name
		self.arity =  len(types)
		self.types = types
		self.isEvidence = (isEvidence == 'evidence')
		self.domain = None

	def associateFunction(self, function):
		self.function = function

	def setDomain(self, domain):
		self.domain =  domain

	def getTypeByIndex(self, index):
		return self.types[index]

