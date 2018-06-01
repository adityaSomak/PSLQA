from types import *
from gurobipy import *

from similarity import *
from pslplus.core import externalfunctions
from pslcore import *


class Predicate(object):

	def __init__(self, template, args, isEvidence=False):
		#print str(args)+", arity:"+str(template.arity)
		if len(args) != template.arity:
			raise Exception('Number of values and tempate-arity does not match')
		typesToCheck = template.types
		i=0
		for arg in args:
			if typesToCheck[i].name == 'STRING' or typesToCheck[i].name == 'UNIQUEID':
				if type(arg) not in {StringType}:
					raise Exception('Should be String. Predicate Creation Failed due to type mismatch at: ',type(arg))
			elif typesToCheck[i].name == 'NUMERIC':
				if type(arg) not in {IntType, FloatType}:
					raise Exception('Should be Numeric. Predicate Creation Failed due to type mismatch at',type(arg))
			i += 1
		self.name = template.name
		self.types = template.types
		self.args = args
		self.isEvidence = isEvidence
		self.domain = None
		self.domainIndex = 0

	'''
	If the predicate has a pre-calculated smaller domain (i.e. set of tuples),
	then set these set of tuples as the predicate's reduced domain.
	'''
	def setDomain(self, evidenceData):
		self.domain = DomainTuple(evidenceData)

	def getFullName(self):
		namestring= self.name+"("
		for i in range(0,len(self.args)-1):
				namestring += self.args[i] + ","
		namestring += self.args[-1]
		namestring += ")"
		return namestring


class Constraint(object):

	def __init__(self, cTemplate, args, relation=None, argC=None):
		typesToCheck = cTemplate.types
		i=0
		for arg in args:
			if typesToCheck[i].name == 'STRING' or typesToCheck[i].name == 'UNIQUEID':
				if type(arg) not in {StringType}:
					raise Exception('Predicate Creation Failed due to type mismatch at',str(i))
			elif typesToCheck[i].name == 'NUMERIC':
				if type(arg) not in {IntType, FloatType}:
					raise Exception('Predicate Creation Failed due to type mismatch at',str(i))
			i+=1
		self.function = cTemplate.function
		self.args = args
		self.relation = relation
		self.argC = argC


class Rule(object):

	'''
	Class for creating a grounded rule object. It also provides a method to translate the
	grounded to rule to Gurobi objectives and constraints.
	'''
	def __init__(self,ruleTemplate, headPredicateMap, bodyPredicateMap, bodyConstraintsMap, nameToTemplateMap, truthvalues = None):
		self.ruleTemplate = ruleTemplate
		'''
		Note: A grounded rule's weight is a Function of rule-template's weight and the similarities.
		As a start: W_gr = alpha1_rt * W_rt + alpha2_rt * W_sim
		'''
		self.grw = 0
		self.bodypredicates = OrderedDict() # name --> [predicate_1, predicate_2 ...]
		self.headpredicates = OrderedDict() # name --> predicate

		self.bodyconstraints = []

		self.truthvalues = truthvalues      # grounded_predicate --> value

		for bTemplateName, pVariablesLists in ruleTemplate.bodypTemplates.items():
			argsLists = bodyPredicateMap[bTemplateName]
			#print bTemplateName + "::" + str(argsLists)
			if argsLists is None:
				raise Exception('Rule grounding failed...')
			self.bodypredicates[bTemplateName] = []
			for i in range(0,len(pVariablesLists)):
				bPredicate = Predicate(nameToTemplateMap[bTemplateName],argsLists[i])
				self.bodypredicates[bTemplateName].append(bPredicate)

		for hTemplateName, pVariables in ruleTemplate.headpTemplates.items():
			args = headPredicateMap[hTemplateName]
			if args is None:
				raise Exception('Rule grounding failed')
			hPredicate = Predicate(nameToTemplateMap[hTemplateName],args)
			self.headpredicates[hTemplateName] = hPredicate

		if bodyConstraintsMap is not None:
			for cName in bodyConstraintsMap:
				constraintPacked = bodyConstraintsMap[cName]
				self.bodyconstraints.add(Constraint(constraintPacked[0], constraintPacked[1],
													constraintPacked[2],constraintPacked[3]))

	def addTruthValuesFromVariableMap(self, m, gurobiVariableMap):
		variablesx = m.getAttr('x', gurobiVariableMap.mapOfVariables)
		self.truthvalues = {}
		for grpredname in variablesx:
			#predname = grpredname[:grpredname.index("(")]
			self.truthvalues[grpredname] = variablesx[grpredname]
		#raise NotImplementedError

	'''
	Supposed to return 1.0-getTruthValue() where
	thruthValue  =
	'''
	def getIncompatibility(self):
		oneMinusdistToSatisfaction = 0
		numberOfPredicates = len(self.bodypredicates.keys())
		bodypredPolarities = self.ruleTemplate.bodypPolarity
		bodypredExtFunctions = self.ruleTemplate.bodypExternalFunction
		headpredPolarities = self.ruleTemplate.headpPolarity
		if self.ruleTemplate.isconstraint:
			for _,bPredicateList in self.bodypredicates.iteritems():
				for i in range(0,len(bPredicateList)):
					bPredicate = bPredicateList[i]
					if bPredicate.name in bodypredExtFunctions:
						oneMinusdistToSatisfaction += (1 / numberOfPredicates) * \
											  externalfunctions.evaluate(bPredicate.name,
																		 self.bodypredicates[bPredicate.name][i].args)
					elif not bodypredPolarities[bPredicate.name][i]:
						oneMinusdistToSatisfaction += (1 / numberOfPredicates) * self.truthvalues[bPredicate.getFullName()]
					else:
						oneMinusdistToSatisfaction += (1 / numberOfPredicates) * (1 - self.truthvalues[bPredicate.getFullName()])
			for _,hPredicate in self.headpredicates.iteritems():
				oneMinusdistToSatisfaction += self.truthvalues[hPredicate.getFullName()]
			return max(1-oneMinusdistToSatisfaction,0)

		oneMinusdistToSatisfaction = 0
		for _,bPredicateList in self.bodypredicates.iteritems():
			for i in range(0, len(bPredicateList)):
				bPredicate = bPredicateList[i]
				if bPredicate.name in bodypredExtFunctions:
					oneMinusdistToSatisfaction += externalfunctions.evaluate(bPredicate.name,
																	 self.bodypredicates[bPredicate.name][i].args)
				elif not bodypredPolarities[bPredicate.name]:
					oneMinusdistToSatisfaction += self.truthvalues[bPredicate.getFullName()]
				else:
					oneMinusdistToSatisfaction += (1 - self.truthvalues[bPredicate.getFullName()])
		if self.ruleTemplate.avgconjrule:
			oneMinusdistToSatisfaction *= (1 / numberOfPredicates)

		for _,hPredicate in self.headpredicates.iteritems():
			if headpredPolarities[hPredicate.name]:
				oneMinusdistToSatisfaction += self.truthvalues[hPredicate.getFullName()]
			else:
				oneMinusdistToSatisfaction += (1 - self.truthvalues[hPredicate.getFullName()])
		#self.grw = W2VPredicateSimilarity.calculateSimilarityOfWords(self.ruleTemplate, self.headpredicates,
		#															 self.bodypredicates)
		# return self.ruleTemplate.getFinalWeight(self.grw) * max(1-distToSatisfaction,0)
		return max(1 - oneMinusdistToSatisfaction, 0)


	def __str__(self):
		finalStr = str(self.ruleTemplate.getFinalWeight(self.grw)) + ", "
		i = 0
		for headPName, hPredicate in self.headpredicates.iteritems():
			if i > 0:
				finalStr += " V "
			finalStr += getString(headPName, hPredicate.args)
			i += 1
		finalStr += "<--"
		i = 0
		for bodyPName, bPredicateLists in self.bodypredicates.iteritems():
			for bPredicate in bPredicateLists:
				if i > 0:
					finalStr += " ^ "
				finalStr += getString(bodyPName, bPredicate.args)
				i += 1
		return finalStr

	'''
	Adds the inference objectives and constraints for this grounded rule
	to Gurobi Model. #Future_TODO: Lets abstract this Later.
	'''
	def addToModel(self, m, gurobiVariableMap, answerVariables, lastRule):

		numberOfPredicates = 0.0
		for _, bPredicateList in self.bodypredicates.iteritems():
			numberOfPredicates += len(bPredicateList)
		conjMultFactor = 1/numberOfPredicates

		bodypredPolarities = self.ruleTemplate.bodypPolarity
		#print bodypredPolarities
		#print self.ruleTemplate.avgconjrule
		bodypredExtFunctions = self.ruleTemplate.bodypExternalFunction
		#print bodypredExtFunctions
		if self.ruleTemplate.isconstraint:
			body = LinExpr()
			for _,bPredicateList in self.bodypredicates.iteritems():
				for i in range(0, len(bPredicateList)):
					bPredicate = bPredicateList[i]
					if bPredicate.name[3:] in bodypredExtFunctions:
						truthValue = externalfunctions.evaluate(bPredicate.name,
																self.bodypredicates[bPredicate.name][i].args)
						body += (1/numberOfPredicates) * gurobiVariableMap.addVariable(
							bPredicate.getFullName(),m, truthValue)
					else:
						variable = gurobiVariableMap.addVariable(
							bPredicate.getFullName(),m, self.truthvalues[bPredicate.getFullName()])
						if bodypredPolarities[bPredicate.name][i] == 'pos':
							body += (1/numberOfPredicates)* variable
						else:
							body += (1/numberOfPredicates)*(1-variable)
			head = LinExpr()
			for _,hPredicate in self.headpredicates.iteritems():
				head += gurobiVariableMap.addVariable(hPredicate.getFullName(),m)
			m.addConstr(head,GRB.GREATER_EQUAL,body)
			return [None,0]

		body = LinExpr()
		externalTruthValues = []
		if self.ruleTemplate.avgconjrule:
			for _,bPredicateList in self.bodypredicates.iteritems():
				for i in range(0, len(bPredicateList)):
					bPredicate = bPredicateList[i]
					if bPredicate.name in bodypredExtFunctions:
						truthValue = externalfunctions.evaluate(bPredicate.name,
																bPredicate.args)
						externalTruthValues.append(truthValue)
						#print "Conj: External value:" + str(truthValue) + ", fn:"+bPredicate.name
						body += conjMultFactor * gurobiVariableMap.addVariable(
							bPredicate.getFullName(),m, truthValue)
					else:
						variable = gurobiVariableMap.addVariable(bPredicate.getFullName(),
																 m, self.truthvalues[bPredicate.getFullName()])
						if bodypredPolarities[bPredicate.name][i]:
							body += conjMultFactor * variable
						else:
							body += conjMultFactor *(1 - variable)
		else:
			for _,bPredicateList in self.bodypredicates.iteritems():
				for i in range(0, len(bPredicateList)):
					bPredicate = bPredicateList[i]
					truthValue = self.truthvalues[bPredicate.getFullName()]
					if bPredicate.name in bodypredExtFunctions:
						truthValue = externalfunctions.evaluate(bPredicate.name,
																bPredicate.args)
						externalTruthValues.append(truthValue)
						#print "External value:" + str(truthValue) + ", fn:" + bPredicate.name
					body += gurobiVariableMap.addVariable(
						bPredicate.getFullName(), m, truthValue)
			body += (1-numberOfPredicates)

		# If similarity is less than threshold, donot add rule.
		# TODO: only true for functions which compute phrase similarity
		avgPhraseSimilarity = 1.0
		if len(externalTruthValues) > 0:
			avgPhraseSimilarity = sum(externalTruthValues)/len(externalTruthValues)
			if avgPhraseSimilarity < 0.4:
				return [None, None, None, None]

		head = LinExpr()
		for _,hPredicate in self.headpredicates.iteritems():
			headVar =  gurobiVariableMap.addVariable(hPredicate.getFullName(),m)
			if lastRule:
				answerVariables[hPredicate.getFullName()] = headVar
			head += headVar

		for constraint in self.bodyconstraints:
			constr = LinExpr()
			constr+= constraint.function(*constraint.args)
			if constraint.relation == "EQ":
				m.addConstr(constr,GRB.EQUAL,constraint.argC)
			elif constraint.relation == "GEQ":
				m.addConstr(constr, GRB.GREATER_EQUAL, constraint.argC)
			elif constraint.relation == "LEQ":
				m.addConstr(constr, GRB.LESS_EQUAL, constraint.argC)

		ruleVarName = ""
		for _, hPred in self.headpredicates.iteritems():
			ruleVarName = ruleVarName + "_" + hPred.getFullName()
		ruleGurobiVariable = m.addVar(lb=0.0, name=ruleVarName)
		#m.update()
		#print head
		#print body
		#m.addConstr(ruleGurobiVariable, GRB.GREATER_EQUAL, 0)
		#m.addConstr(ruleGurobiVariable, GRB.GREATER_EQUAL, body-head)
		self.grw = 1.0
		#self.grw = avgPhraseSimilarity
		#W2VPredicateSimilarity.calculateSimilarityOfWords(self.ruleTemplate, self.headpredicates,self.bodypredicates)
		#print ruleVarName+":"+str(self.ruleTemplate.getFinalWeight(self.grw))
		#m.update()
		return [ruleGurobiVariable, self.ruleTemplate.getFinalWeight(self.grw), body, head]

def getString(predicateName, arguments):
	return predicateName + "(" + ",".join(arguments) + ")"

class GurobiVariableMap(object):
	def __init__(self):
		self.mapOfVariables = dict()

	def addVariable(self, variableName, m, truthValue=None):
		try:
			gurobiVar = self.mapOfVariables[variableName]
		except KeyError:
			if truthValue is not None:
				gurobiVar = m.addVar(lb=truthValue, ub=truthValue, name=variableName)
			else:
				gurobiVar = m.addVar(lb=0.0, ub=1.0, name=variableName)
			self.mapOfVariables[variableName] = gurobiVar
		return gurobiVar

	def addConstraint(self, variableName, m, lb, ub):
		gurobiVar = self.mapOfVariables[variableName]
		m.addConstr(gurobiVar,GRB.GREATER_EQUAL,lb)
		m.addConstr(ub,GRB.GREATER_EQUAL,gurobiVar)