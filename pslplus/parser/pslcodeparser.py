import re
from pslplus.core import pslcore
from pslplus.core import rulebase
from pslplus.core.pslcore import *
from pslplus.core.domain import *

'''
    # From question
	topic(UNIQUEID).
	conditions(UNIQUEID).
	condition_rel(STRING).
	condition_pair(STRING, UNIQUEID).
	path(STRING, NUMERIC).
	path_contains(STRING,STRING).

	rel(UNIQUEID, STRING, UNIQUEID).

	# 1.ii) Define the Predicate-templates (Inference)
	exists(UNIQUEID) :-
	existsP(UNIQUEID, STRING, UNIQUEID, NUMERIC) :-
	relation_chain_holds(UNIQUEID, STRING, UNIQUEID) :-
	answer(UNIQUEID, STRING, UNIQUEID) :-

	exists(T) :: topic(T).
	existsP(X,P,T,2) :: topic(T) ^ path_contains(P,R,1) ^ rel(T,R,X).
	existsP(X1,P,T,K+1) :: exists(X) ^ path_contains(P,R,K) ^ rel(X,R,X1).
	relation_chain_holds(T,P,Y) :: existsP(Y,P,T,N) ^ path(P,N).
	answer(Y,P,T) :: relation_chain_holds(T,P,Y) ^ getObjecttype(Y) == answertype.
'''


def parsePSLTemplates(pslcodefile):
    evidencePredicateTemplates = {}
    inferencePredicateTemplates ={}
    ruleBase = rulebase.RuleBase()

    nameToArgumentType = {}
    for name, member in ArgumentType.__members__.items():
        nameToArgumentType[name] = member

    with open(pslcodefile,'r') as pslcode:
        for line in pslcode:
            line = line.replace("\n","")
            # print line
            if line == '' or line.startswith("#"):
                continue
            if line.endswith("."):
                if "::" not in line:
                    # populate evidence predicates
                    tokens = re.split(r"[\(\)]",line)
                    types = []
                    typenames = tokens[1].split(",")
                    for i in range(0, len(typenames)):
                        types.append(nameToArgumentType[typenames[i].strip()])
                    evidencePredicateTemplates[tokens[0]] = pslcore.PredicateTemplate(tokens[0], types, 'evidence')
                    ruleBase.addPredicateTemplate(tokens[0],types)
                else:
                    # populate Rule
                    variables = {}
                    m = re.search('^(\d+\.\d+)\, (.+)', line)
                    if m is not None:
                        weight = float(m.group(1))
                        line = m.group(2)
                        nextRule = ruleBase.addRuleTemplates(True, weight)
                    else:
                        nextRule = ruleBase.addRuleTemplates(True, 10.0)
                    #print ruleBase.pTemplateMap.pTemplateMap
                    headAndBody = re.split(r"::",line)
                    headPredicates = re.split(r"||",headAndBody[0])
                    bodyPredicates = re.split(r"\^",headAndBody[1])
                    # print headPredicates
                    # print bodyPredicates

                    # populate body-predicates
                    for predicateStr in bodyPredicates:
                        tokens = re.split(r"[\(\)]", predicateStr.replace("\.","").strip())
                        isNeg = 'pos'
                        if tokens[0].strip().startswith("not "):
                            tokens[0] = tokens[0].strip()[4:]
                            isNeg = 'neg'
                        variableNames = tokens[1].split(",")
                        predVariables = []
                        index = 0
                        # get the variables T, P, X
                        for name in variableNames:
                            name = name.strip()
                            if name.islower():
                                newVar = Constant(name, evidencePredicateTemplates[tokens[0]].getTypeByIndex(index),name)
                                variables[name] = newVar
                                predVariables.append(newVar)
                            elif name in variables:
                                predVariables.append(variables[name])
                            else:
                                newVar = Variable(name, evidencePredicateTemplates[tokens[0]].getTypeByIndex(index))
                                variables[name] = newVar
                                predVariables.append(newVar)
                            index +=1
                        nextRule.addBodyPredicate(evidencePredicateTemplates[tokens[0]], predVariables, isNeg)

                    # populate head-predicates
                    for predicateStr in headPredicates:
                        tokens = re.split(r"[\(\)]", predicateStr.replace("\.","").strip())
                        types = []
                        variableNames = tokens[1].split(",")
                        predVariables = []
                        index = 0
                        # get the variables T, P, X
                        for name in variableNames:
                            name = name.strip()
                            predVariables.append(variables[name])
                            index +=1
                        nextRule.addHeadPredicate(inferencePredicateTemplates[tokens[0]], predVariables)
            else:
                # populate inference predicates
                tokens = re.split(r"[\(\)]", line)
                types = []
                typenames = tokens[1].split(",")
                for i in range(0, len(typenames)):
                    types.append(nameToArgumentType[typenames[i].strip()])
                inferencePredicateTemplates[tokens[0]] = pslcore.PredicateTemplate(tokens[0], types, 'inference')
                evidencePredicateTemplates[tokens[0]] = inferencePredicateTemplates[tokens[0]]
                ruleBase.addPredicateTemplate(tokens[0], types)
    return ruleBase, evidencePredicateTemplates
