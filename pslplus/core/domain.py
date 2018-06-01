import numpy as np
import numpy.ma as ma
from enum import Enum

class ArgumentType(Enum):
	STRING = 1
	NUMERIC = 2
	UNIQUEID = 3


class Domain(object):
	def __init__(self, name, type):
		self.name = name
		if type == ArgumentType.STRING or type == ArgumentType.UNIQUEID:
			self.data = np.empty(0, dtype='str')
		else:
			self.data = np.empty(0, dtype='int')
		self.truthvalues = None
		self.dataToIndexDict = {}
		self.type = type

	def addElement(self, element):
		self.data = np.append(self.data, element)

	def setData(self, data, truthvalues=None):
		self.data = data
		index = 0
		for tupleString in data:
			self.dataToIndexDict[tupleString] = index
			index += 1
		if truthvalues is not None:
			self.truthvalues = truthvalues

	def getTruthValue(self, args):
		key = ",".join(args)
		try:
			return self.truthvalues[self.dataToIndexDict[key]]
		except KeyError:
			return None

	def getData(self):
		return self.data

	def getLength(self):
		return len(self.data)

class SubDomain(Domain):
	def __init__(self, name, type, data):
		Domain.__init__(self, name, type)
		self.setData(data)
		self.mask =  False

	def setMask(self,mask):
		self.mask = mask

	def getData(self):
		return ma.array(self.data, mask=self.mask)


class DomainTuple(object):
	def __init__(self, name, dataTuples=None):
		self.name = name
		self.data = None  # np.array(dataTuples);
		self.iterationIndex = 0

	def setData(self, dataTuples):
		self.data = np.array(dataTuples)

	def getNextCombination(self):
		if self.iterationIndex >= self.getLength():
			return None
		tupleD = self.data[self.iterationIndex:]
		self.iterationIndex += 1
		return tupleD

	def getCurrentCombination(self):
		if self.iterationIndex >= self.getLength():
			return None
		return self.data[self.iterationIndex:]

	def resetIteration(self):
		self.iterationIndex = 0

	def isIterationComplete(self):
		return  self.iterationIndex >= self.getLength()

	def getLength(self):
		return self.data.shape[0]
