from groundedrule import Rule, GurobiVariableMap
from gurobipy import *
from grounding import *
import numpy as np

def infer(ruleBase, variableSuperDomainMap, predDB, nameToTemplateMap, iteration,
		  S_ANS=20.0, S_CAND=20.0):
	m = Model("psl1")
	m.setParam(GRB.Param.LogFile, "")
	gurobiVariableMap = GurobiVariableMap()
	objective = LinExpr()
	summarytablesAlreadyCreated = set()
	lastRule = False
	answerVariables = {}
	answerCandVariables = {}
	for i_rule, ruleT in enumerate(ruleBase.ruleTemplates):
		allVariablesInRule = {}
		pNameToVarNamesMap = {}
		pNameToVariablesMap = {}
		for bName, bTemplateVariablesLists in ruleT.bodypTemplates.items():
			for i, variables in enumerate(bTemplateVariablesLists):
				for var in variables:
					if var not in allVariablesInRule:
						allVariablesInRule[var.name] = var
				if not bName.startswith("Fn_"):
					pNameToVarNamesMap[bName+"_"+str(i)] = [var.name for var in variables]
					pNameToVariablesMap[bName+"_"+str(i)] = variables
		print pNameToVarNamesMap
		'''
		6. Use the class CombinationGenerator - which generates combination
		based on predicate templates and variable-domains.
		'''
		combinationGenerator = CombinationGenerator(
			allVariablesInRule, predDB, pNameToVarNamesMap,
			pNameToVariablesMap, summarytablesAlreadyCreated,
			variableSuperDomainMap, nameToTemplateMap,
			ruleT)
		combinedHeadPredicateMap = {}
		[headPredicateMap, bodyPredicateMap, bodyConstraintsMap, truthvalues] = \
			combinationGenerator.getNewCombination2()
		rulevariables = []
		bodyMHead = []
		if headPredicateMap is not None:
			if ("ans" in headPredicateMap.keys()) or ("ans_candidate" in headPredicateMap.keys()):
				lastRule = True
			else:
				lastRule = False
		while headPredicateMap is not None:
			for template in headPredicateMap:
				try:
					combinedHeadPredicateMap[template].add(",".join(headPredicateMap[template]))
				except KeyError:
					combinedHeadPredicateMap[template] = {",".join(headPredicateMap[template])}
			rule = Rule(ruleT, headPredicateMap, bodyPredicateMap, bodyConstraintsMap, nameToTemplateMap, truthvalues)
			if "ans" in headPredicateMap.keys():
				[ruleGurobiVariable,weight,body, head] = rule.addToModel(m, gurobiVariableMap, answerVariables, lastRule)
			elif "ans_candidate" in headPredicateMap.keys():
				[ruleGurobiVariable, weight, body, head] = rule.addToModel(m, gurobiVariableMap, answerCandVariables,
																		   lastRule)
			else:
				[ruleGurobiVariable, weight, body, head] = rule.addToModel(m, gurobiVariableMap, {}, False)
			if ruleGurobiVariable is not None:
				ruleT.addGroundedRule(rule)
				bodyMHead.append((body,head))
				rulevariables.append(ruleGurobiVariable)
				objective += weight*ruleGurobiVariable
			[headPredicateMap, bodyPredicateMap, bodyConstraintsMap, truthvalues] = combinationGenerator.getNewCombination2()

		predDB.insertHeadTemplateTables(combinedHeadPredicateMap)
		m.update()
		for i, ruleGurobiVariable in enumerate(rulevariables):
			m.addConstr(ruleGurobiVariable, GRB.GREATER_EQUAL, 0)
			m.addConstr(ruleGurobiVariable, GRB.GREATER_EQUAL, bodyMHead[i][0]-bodyMHead[i][1])

	# NOTE: without this, it gives good results for ans_candidate
	#  20.0 and 10.0 gives good results
	# {
	m.addConstr(quicksum(answerCandVariables[c1] for c1 in answerCandVariables), GRB.LESS_EQUAL, S_ANS)
	# NOTE: Use 10.0 to reproduce expt2 in aaai18
	if len(answerVariables) > 0:
		for c1 in answerVariables:
			ansCandV = answerCandVariables[c1.replace("ans(","ans_candidate(")]
			m.addConstr(ansCandV, GRB.GREATER_EQUAL, answerVariables[c1])
		m.addConstr(quicksum(answerVariables[c1] for c1 in answerVariables), GRB.LESS_EQUAL, S_CAND)
		# NOTE: Use 10.0 to reproduce expt2 in aaai18
	# }
	m.setObjective(objective)

	# The objective is to minimize the costs
	m.modelSense = GRB.MINIMIZE
	# Update model to integrate new variables
	m.update()

	m.optimize()
	# if iteration%10 == 0:
	# 	m.write("model"+str(iteration)+".lp")
	# 	solF = open("model"+str(iteration)+".sol",'w')
	# 	solF.write('Solution:\n')
	# 	variablesx = m.getAttr('X', gurobiVariableMap.mapOfVariables)
    #
	# 	for grpredname in variablesx:
	# 		solF.write(grpredname+"="+str(variablesx[grpredname])+"\n")
	# 	solF.close()

	#for ruleT in ruleBase.ruleTemplates:
	#	for groundedRule in ruleT.getGroundedRules():
	#		groundedRule.addTruthValuesFromVariableMap(m,gurobiVariableMap)
	answerVariables.update(answerCandVariables)
	return [m, gurobiVariableMap, answerVariables, summarytablesAlreadyCreated]

def inferHeadVariables(ruleBase, domainMap, predDB, nameToTemplateMap, S_CAND=20.0):
	[m, gurobiVariableMap, answerVariables, summarytablesAlreadyCreated] = \
		infer(ruleBase, domainMap, predDB, nameToTemplateMap, 0, S_CAND=S_CAND)

	headVariablesDict = {}
	# for ruleT in ruleBase.ruleTemplates:
	# 	for groundedRule in ruleT.getGroundedRules():
	# 		for hPred in groundedRule.headpredicates:
	# 			headVariablesDict[hPred.getFullName()] = gurobiVariableMap[hPred.getFullName()]
	variablesx = m.getAttr('X', answerVariables)
	for varName in variablesx:
		headVariablesDict[varName] = variablesx[varName]
	return [headVariablesDict, summarytablesAlreadyCreated]


def computeExpectedIncomp(ruleBase, domainMap, nameToTemplateMap, iteration):
	infer(ruleBase, domainMap, nameToTemplateMap, iteration)

	expectedIncompatitbility = np.zeros((len(ruleBase.ruleTemplates)))
	grIncompatibilities = {}
	numGrounding = np.zeros((len(ruleBase.ruleTemplates)))
	i = 0
	for kernel in ruleBase.ruleTemplates:
		grIncompatibilities[i] = []
		for groundedRule in kernel.getGroundedRules():
			incomp = groundedRule.getIncompatibility()
			expectedIncompatitbility[i] += incomp
			grIncompatibilities[i].append(incomp)
			numGrounding[i] += 1
		i += 1

	return expectedIncompatitbility, numGrounding, grIncompatibilities

def computeObservedIncomp(ruleBase, trainingDomainMap, nameToTemplateMap, predDB, printRulesToFile=False):
	calculateGroundedRules(ruleBase, trainingDomainMap, nameToTemplateMap, predDB, printRulesToFile)

	observedIncompatibility = np.zeros((len(ruleBase.ruleTemplates)))
	grIncompatibilities = {}
	numGrounding = np.zeros((len(ruleBase.ruleTemplates)))
	i = 0
	for kernel in ruleBase.ruleTemplates:
		grIncompatibilities[i] = []
		for groundedRule in kernel.getGroundedRules():
			incomp = groundedRule.getIncompatibility()
			observedIncompatibility[i] += incomp
			grIncompatibilities[i].append(incomp)
			numGrounding[i] += 1
		i += 1

	return observedIncompatibility, numGrounding, grIncompatibilities

'''
 If has_q(A,B,C) is a predicate, then
@:param trainingDataMap :
    has_q -> [[dog, has, tail] , [man, has, legs] ....]
          -> [1.0, 1.0, 0.8, ....]
'''
def calculateGroundedRules(ruleBase, trainingDomainMap, nameToTemplateMap, predDB, printRules = False):
	fileToPrint = None
	if printRules:
		fileToPrint = open("/home/somak/grRules.txt",'w')
	summarytablesAlreadyCreated = set()
	for ruleT in ruleBase.ruleTemplates:
		'''
		6. Use the class CombinationGenerator - which generates combination
		based on predicate templates and variable-domains.
		'''
		allVariablesInRule = {}
		pNameToVarNamesMap = {}
		pNameToVariablesMap = {}
		for bName, bTemplateVariablesLists in ruleT.bodypTemplates.items():
			for i, variables in enumerate(bTemplateVariablesLists):
				for var in variables:
					if var not in allVariablesInRule:
						allVariablesInRule[var.name] = var
				if not bName.startswith("Fn_"):
					pNameToVarNamesMap[bName + "_" + str(i)] = [var.name for var in variables]
					pNameToVariablesMap[bName + "_" + str(i)] = variables
		print pNameToVarNamesMap
		combinationGenerator = CombinationGenerator(
			allVariablesInRule, predDB, pNameToVarNamesMap,
			pNameToVariablesMap, summarytablesAlreadyCreated,
			trainingDomainMap, nameToTemplateMap,
			ruleT)
		[headPredicateMap, bodyPredicateMap, bodyConstraintsMap, truthvaluesMap] = \
			combinationGenerator.getNewCombination2()
		while bodyPredicateMap is not None and len(bodyPredicateMap) > 0:
			if headPredicateMap is not None:
				rule = Rule(ruleT, headPredicateMap, bodyPredicateMap,
							bodyConstraintsMap, nameToTemplateMap, truthvaluesMap)
				if printRules:
					fileToPrint.write(rule.__str__())
					fileToPrint.write("\n")
				ruleT.addGroundedRule(rule)
			[headPredicateMap, bodyPredicateMap, bodyConstraintsMap, truthvaluesMap] = \
				combinationGenerator.getNextIteration()
			combinationGenerator.cleanup()

	if printRules:
		fileToPrint.close()