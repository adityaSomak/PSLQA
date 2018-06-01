from Queue import Empty
from multiprocessing import Process, Queue

import externalfunctions
from pslcore import ExpressionVariable
from pslplus.core.db.RecursiveCombinationTupleGenerator2 import RecursiveCombinationTupleGeneratorFast as FastRecursion


class CombinationGenerator(object):
	'''
	  Example: rel_exists(R,Y,T) :- 
	  				path_contains(P,R) ^ answer(P,Y,T).
	  allVariables: P, R, Y, T
	  answer has answer.Domain not None
	'''
	def __init__(self, allVariables, predDB, pNameToVarNamesMap, pNameToVariablesMap, summarytablesAlreadyCreated,
				 trainingDomainMap, nameToTemplateMap, ruleT):
		self.allVariables = allVariables
		self.predicatesDB = predDB
		self.pNameToVarNamesMap = pNameToVarNamesMap
		self.pNameToVariablesMap = pNameToVariablesMap
		self.summarytablesAlreadyCreated = summarytablesAlreadyCreated
		self.trainingDomainMap = trainingDomainMap
		self.nameToTemplateMap = nameToTemplateMap
		self.ruleT = ruleT

		self.variablePositionMap = {}
		self.variableDomainMap = {}

		#self.startIteration()
		self.startIteration2()

	def startIteration2(self):
		self.tupleGenerator = FastRecursion(self.predicatesDB, self.pNameToVarNamesMap,
											self.pNameToVariablesMap, self.summarytablesAlreadyCreated)
		self.resultsIterator = self.tupleGenerator.getResultsFromSummaryTable()

	def getNewCombination2(self):
		try:
			newCombination = next(self.resultsIterator)
		except StopIteration:
			return [None,None,None,None]
		variableNamesToValues = {}
		for i,varName in enumerate(self.tupleGenerator.variableNames):
			variableNamesToValues[varName] = str(newCombination[i])

		[truthvalues, bodyPredicateMap] = self.getConsistentBodyPredicates(variableNamesToValues)
		headPredicateMap = {}
		for hTemplateName in self.ruleT.headpTemplates:
			templateVariables = self.ruleT.headpTemplates[hTemplateName]
			args = []
			for var in templateVariables:
				args.append(variableNamesToValues[var.name])
			headPredicateMap[hTemplateName] = args
		return [headPredicateMap, bodyPredicateMap, None, truthvalues]

	def startIteration(self):
		self.varToDomainVariablesMap = {} #

		for bodypName in self.ruleT.bodypTemplates:
			variablesList = self.ruleT.bodypTemplates[bodypName]
			for variables in variablesList:
				pos = 0
				for var in variables:
					try:
						self.variablePositionMap[var.name][bodypName] = pos
					except KeyError:
						self.variablePositionMap[var.name] = {bodypName: pos}
					pos += 1
		print self.variablePositionMap

		# Now get the individual domains:
		# varA: {1,2}
		# varB: {1,2}
		for tempName in self.trainingDomainMap:
			if tempName == "head":
				continue
			for varName in self.variablePositionMap:
				if tempName in self.variablePositionMap[varName]:
					try:
						setofValues = self.variableDomainMap[varName]
					except KeyError:
						setofValues = set()
						self.variableDomainMap[varName] = setofValues
						self.varToDomainVariablesMap[varName] = [varName]
					position = self.variablePositionMap[varName][tempName]
					tuples = self.trainingDomainMap[tempName][0]
					for tuple in tuples:
						value = tuple.split(",")[position]
						setofValues.add(value)

		self.tupleGenerator = RecursiveCombinationTupleGenerator(self.variableDomainMap)
		self.numCombinationsToTry = self.tupleGenerator.totalPossibleCominations

	def getNewCombination(self):
		variableNamesToValues = {}

		nextCombination = None
		while nextCombination is None:
			self.numCombinationsToTry -= 1
			if self.numCombinationsToTry <= 0:
				return [None,None,None,None]
			nextCombination = self.tupleGenerator.getNextTuple()

			if nextCombination is not None:
				for varName in self.tupleGenerator.variableNames:
					# if from predicate-domain, its a tuple.
					varTuple = nextCombination[varName].split(",")
					index = self.varToDomainVariablesMap[varName].index(varName)
					variableNamesToValues[varName] = varTuple[index]

				[truthvalues, bodyPredicateMap] = self.getConsistentBodyPredicates(variableNamesToValues)
				if truthvalues is None:
					nextCombination = None
		headPredicateMap = {}
		for hTemplateName in self.ruleT.headpTemplates:
			templateVariables = self.ruleT.headpTemplates[hTemplateName]
			args=[]
			for var in templateVariables:
				args.append(variableNamesToValues[var.name])
			headPredicateMap[hTemplateName] = args
			# truthvalues[hTemplateName + "_".join(args)] = self.ruleT.headpTemplates[hTemplateName].domain.getTruthValue(args)
		'''
			TODO build body constraint arguments
		'''
		return [headPredicateMap, bodyPredicateMap, None, truthvalues]

	def getConsistentBodyPredicates(self, variableNamesToValues):
		truthvalues = {}
		bodyPredicateMap = {}
		for bTemplateName in self.ruleT.bodypTemplates:
			templateVariablesList = self.ruleT.bodypTemplates[bTemplateName]
			reusedHeadPredicate = (self.nameToTemplateMap[bTemplateName].domain is None)
			bodyPredicateMap[bTemplateName] = []
			for templateVariables in templateVariablesList:
				args = []
				for var in templateVariables:
					if isinstance(var, ExpressionVariable):
						expressionargs = []
						for depVar in var.dependentVariables:
							expressionargs.append(variableNamesToValues[depVar.name])
						args.append(var.getValue(expressionargs))
					args.append(variableNamesToValues[var.name])
				if reusedHeadPredicate:
					# i.e. a body predicate which is also a head predicate
					# in some other rule
					truthvalues[bTemplateName + "(" + ",".join(args) + ")"] = None
					bodyPredicateMap[bTemplateName].append(args)
				else:
					try:
						queryString = ",".join(args)
						index = self.trainingDomainMap[bTemplateName][0].index(queryString)
					except ValueError:
						print "Exception on::::"
						print variableNamesToValues
						print ",".join([var.name for var in templateVariables])
						print bTemplateName+":"+ ",".join(args)
						print "Reused head predicate:" + str(reusedHeadPredicate)
						return [None, None]
					truthvalues[bTemplateName + "(" + ",".join(args) + ")"] = \
						self.trainingDomainMap[bTemplateName][1][index]
					bodyPredicateMap[bTemplateName].append(args)
		return [truthvalues, bodyPredicateMap]

class CombinationGeneratorFromTrainingData(object):

	def __init__(self, trainingDomainMap, ruleT):
		self.trainingDomainMap = trainingDomainMap
		self.ruleT = ruleT
		self.variablePositionMap = {}
		self.variableDomainMap = {}
		self.startIteration()

	def startIteration(self):
		# For rule SamePerson(A,B) :: Network(A, snA) ^ Network(B, snB) ^ Name(A,X) ^ Name(B,Y) ^ Fn_SameName(X,Y)
		# varA : {Network: 1, Name: 1}
		# varB : {Network: 1, Name: 1}
		for bodypName in self.ruleT.bodypTemplates:
			variablesList = self.ruleT.bodypTemplates[bodypName]
			for variables in variablesList:
				pos = 0
				for var in variables:
					try:
						self.variablePositionMap[var.name][bodypName] = pos
					except KeyError:
						self.variablePositionMap[var.name] = {bodypName: pos}
					pos += 1
		print self.variablePositionMap

		# Now get the individual domains:
		# varA: {1,2}
		# varB: {1,2}
		for tempName in self.trainingDomainMap:
			if tempName == "head":
				continue
			for var in self.variablePositionMap:
				if tempName in self.variablePositionMap[var]:
					try:
						setofValues = self.variableDomainMap[var]
					except KeyError:
						setofValues = set()
						self.variableDomainMap[var] = setofValues
					position = self.variablePositionMap[var][tempName]
					tuples = self.trainingDomainMap[tempName][0]
					for tuple in tuples:
						value = tuple.split(",")[position]
						setofValues.add(value)
		self.tupleGenerator = RecursiveCombinationTupleGenerator(self.variableDomainMap)
		self.numCombinationsToTry = self.tupleGenerator.totalPossibleCominations

	'''
	  TODO: This code is incomplete, refactor and re-write
	'''
	def getNextIteration(self):

		headPredicateMap = {}
		groundedbodyPredicateMap = None
		truthvaluesMap = None

		while groundedbodyPredicateMap is None:
			currentVariables = self.getNextVariableTuple()
			self.numCombinationsToTry -= 1
			if currentVariables is None:
				if self.numCombinationsToTry <= 0:
					return [None,None,None,None]
				else:
					groundedbodyPredicateMap = None
			else:
				[groundedbodyPredicateMap,truthvaluesMap] = self.getConsistentBodyPredicateMap(currentVariables)

		# head_predicate_templateName
		for headp_TName in self.ruleT.headpTemplates:
			queryTuple = self.ruleT.getHeadPredicateTuple(groundedbodyPredicateMap, headp_TName)
			queryTupleString = ",".join(queryTuple)
			key = headp_TName + "(" + queryTupleString + ")"
			try:
				truthvaluesMap[key] = self.trainingDomainMap["head"][headp_TName][queryTupleString]
			except KeyError:
				truthvaluesMap[key] = 0.0
			headPredicateMap[headp_TName] = queryTuple

		return [headPredicateMap, groundedbodyPredicateMap , None, truthvaluesMap]

	def cleanup(self):
		for g in self.tupleGenerator.generator:
			g.terminate()

	'''
		Call RecursiveCombinationTupleGenerator.getNextTuple to get the
		next combination for the set of variable sin the rule.
	'''
	def getNextVariableTuple(self):
		return self.tupleGenerator.getNextTuple()

	'''
		Given variable values, check if they are in training data.
		i.e. A =1, B=2, Knows(1,2) in training data or not.
	'''
	def getConsistentBodyPredicateMap(self,currentVariables):
		groundedbodyPredicateMap = {}
		truthvaluesMap = {}
		for bodypTemplateName in self.ruleT.bodypTemplates:
			variablesLists = self.ruleT.bodypTemplates[bodypTemplateName]
			groundedTupleList = []
			truthValueList = []
			for variables in variablesLists:
				querytuple = [currentVariables[var.name] for var in variables]
				queryString = ",".join(querytuple)
				if bodypTemplateName in self.ruleT.bodypExternalFunction:
					#print querytuple
					truthValueList.append(externalfunctions.evaluate(bodypTemplateName,
						querytuple))
					groundedTupleList.append(querytuple)
				else:
					try:
						tupleIndex = self.trainingDomainMap[bodypTemplateName][0].index(queryString)
						truthValueList.append(self.trainingDomainMap[bodypTemplateName][1][tupleIndex])
						groundedTupleList.append(queryString.split(","))
					except ValueError:
						return [None,None]
			groundedbodyPredicateMap[bodypTemplateName] = groundedTupleList
			for i in range(0, len(groundedTupleList)):
				key = bodypTemplateName+"("+",".join(groundedTupleList[i])+")"
				truthvaluesMap[key] = truthValueList[i]

		return [groundedbodyPredicateMap,truthvaluesMap]

class RecursiveCombinationTupleGenerator(object):

	def __init__(self, mapOfLists):
		self.variableNames = [k for k in mapOfLists]
		self.allLists = [list(mapOfLists[k]) for k in self.variableNames]
		self.totalPossibleCominations = 1
		for lst in self.allLists:
			self.totalPossibleCominations *= len(lst)
			print "Length of list:" + str(len(lst))
		self.Result = Queue()
		print "Number of Combinations to Try:"+str(self.totalPossibleCominations)
		# TODO: (DEBUG) run this next line parallely
		self.generator = [Process(target=self.generatePermutation, args=(0, self.Result, [],))
                        for i in xrange(1)]
		for g in self.generator:
			g.start()
		#self.generatePermutation(0,self.Result, [])
		#self.startIndex = 0

	def getNextTuple(self):
		currentVariables = {}
		i = 0
		#if len(self.Result) < self.index:
			# wait for thread a few seconds

		# TODO: (DEBUG)
		# Result.get() waits for the thread to populate the next produced item
		try:
			# TODO: Re-think hack. consumer waits 5 seconds for the producer to
			# populate.
			varValues = self.Result.get(True,5)
			#print varValues
			for var in self.variableNames:
				currentVariables[var] = varValues[i]
				i += 1
			return currentVariables
		except Empty:
			return None

	def generatePermutation(self, depth, result, current):
		if depth == len(self.allLists):
			result.put(current)
			return

		#print "Depth: "+str(depth)+";Current: "+current
		for i in range(0, len(self.allLists[depth])):
			new_current = []
			new_current.extend(current)
			new_current.append(self.allLists[depth][i])
			self.generatePermutation(depth+1, result, new_current)
