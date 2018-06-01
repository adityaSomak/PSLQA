from pslplus.core import pslcore
from pslplus.core import pslground
from pslplus.core import rulebase
from pslplus.externalfunctions import *
from pslplus.core.pslcore import *
from pslplus.core.domain import *


def loadFromTSVData(tsvFileName, expectedColumns):
    dataTuples = []
    truthvalues = []
    with open(tsvFileName, 'r') as f:
        for line in f:
            tokens = line.split("\t")
            dataTuples.append(tokens[0:expectedColumns])
            truthvalues.append(tokens[expectedColumns])
    return dataTuples, truthvalues


def getVariables(varNames, varTypes, optionalValues=None):
    variables = []
    for i in range(len(varNames)):
        if varTypes[i] == ArgumentType.NUMERIC and optionalValues != None and optionalValues[i] != None:
            var = Variable(varNames[i], varTypes[i], optionalValues[i])
        else:
            var = Variable(varNames[i], varTypes[i])
        variables.append(var)
    return variables


def run():
    '''
        1.i) Define the Predicate-templates (Evidence)
        %%%% From question %%%%
        topic(t1t2...tm).
        conditions(z1z2...zm).
        condition_rel(r1r2...).
        condition_pair(r1,z1).
        ...
        conditon_pair(rk,zl).
        path(p1,l1).
        path(p2,l2).
        ...
        path(pn,ln).
        path_contains(p1,r11)
        ...
        path_contains(pn,rnk)
        %%%% From Freebase %%%%
        rel(e1,r1,e2)
        ...
        rel(eN-1,rM,eN)
    '''
    topicT = pslcore.PredicateTemplate('topic', [ArgumentType.UNIQUEID], 'evidence')
    conditionT = pslcore.PredicateTemplate('condition', [ArgumentType.UNIQUEID], 'evidence')
    pathT = pslcore.PredicateTemplate('path', [ArgumentType.STRING, ArgumentType.NUMERIC], 'evidence')
    pathcontainsT = pslcore.PredicateTemplate('path_contains', [ArgumentType.STRING, ArgumentType.STRING], 'evidence')
    condition_relT = pslcore.PredicateTemplate('condition_rel', [ArgumentType.STRING], 'evidence')
    condition_pairT = pslcore.PredicateTemplate('condition_pair', [ArgumentType.STRING, ArgumentType.UNIQUEID], 'evidence')
    relationsT = pslcore.PredicateTemplate('rel', [ArgumentType.UNIQUEID, ArgumentType.STRING,
                                                   ArgumentType.UNIQUEID], 'evidence')

    '''
        1.ii) Define the Predicate-templates (Inference)
        exists(T) :-
        existsP(X,P,T,K+1) :-
        relation_chain_holds(T,P,Y) :-
        answer(Y,P,T) :-
        relation_exists(R,Y,T) :-
        ent_exists(X1,Y,T) :-
        pair_exists(R,X1,Y,T) :-
        not_final_answer(Y,T) :-
        final_answer(Y) :-
    '''
    existsT = pslcore.PredicateTemplate('exists', [ArgumentType.UNIQUEID], 'inference')
    existsPT = pslcore.PredicateTemplate('existsP', [ArgumentType.UNIQUEID, ArgumentType.STRING,
                                                     ArgumentType.UNIQUEID, ArgumentType.NUMERIC], 'inference')
    relation_chain_holdsT = pslcore.PredicateTemplate('relation_chain_holds', [ArgumentType.UNIQUEID,
                                                                               ArgumentType.STRING, ArgumentType.UNIQUEID],
                                                      'inference')
    answerT = pslcore.PredicateTemplate('answer', [ArgumentType.UNIQUEID, ArgumentType.STRING,
                                                   ArgumentType.UNIQUEID], 'inference')
    relation_existsT = pslcore.PredicateTemplate('relation_exists', [ArgumentType.STRING, ArgumentType.STRING,
                                                                     ArgumentType.UNIQUEID], 'inference')
    ent_existsT = pslcore.PredicateTemplate('ent_exists', [ArgumentType.UNIQUEID, ArgumentType.STRING,
                                                           ArgumentType.UNIQUEID], 'inference')
    pair_existsT = pslcore.PredicateTemplate('pair_exists', [ArgumentType.STRING, ArgumentType.UNIQUEID,
                                                             ArgumentType.UNIQUEID], 'inference')
    not_final_answerT = pslcore.PredicateTemplate('not_final_answer', [ArgumentType.UNIQUEID, ArgumentType.UNIQUEID],
                                                  'inference')
    final_answerT = pslcore.PredicateTemplate('final_answer', [ArgumentType.UNIQUEID], 'inference')

    '''
        2. Define variables and rules
        (i) exists(T) :- topic(T).
    '''
    varT = Variable('T', ArgumentType.UNIQUEID)
    ruleBase = rulebase.RuleBase()
    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(topicT, [varT])
    nextRule.addHeadPredicate(existsT, [varT])

    '''
        (ii).1 existsP(X,P,T,2) :- topic(T) ^ path_contains(P,R,1) ^ rel(T,R,X).
    '''
    [varX, varP, varT, varR, var1, var2] = getVariables(
        ['X', 'P', 'T', '1', 'R', '2'],
        [ArgumentType.UNIQUEID, ArgumentType.STRING, ArgumentType.UNIQUEID, ArgumentType.STRING,
            ArgumentType.NUMERIC, ArgumentType.NUMERIC],
        [None, None, None, None, 1, 2])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)

    nextRule.addBodyPredicate(topicT, [varT])
    nextRule.addBodyPredicate(pathcontainsT, [varP, varR, var1])
    nextRule.addBodyPredicate(relationsT, [varT, varR, varX])
    nextRule.addHeadPredicate(existsPT, [varX, varP, varT, var2])
    '''
        (ii).2 existsP(X1,P,T,K+1) :- exists(X) ^ path_contains(P,R,K) ^ rel(X,R,X1).
    '''
    [varX, varX1, varP, varT, varK] = getVariables(
        ['X', 'X1', 'P', 'T', 'K'],
        [ArgumentType.UNIQUEID, ArgumentType.UNIQUEID, ArgumentType.STRING, ArgumentType.UNIQUEID, ArgumentType.NUMERIC])
    varKp1 = ExpressionVariable('K+1', [varK], "K+1")
    nextRule = ruleBase.addRuleTemplate(True, 10.0)

    nextRule.addBodyPredicate(existsT, [varX])
    nextRule.addBodyPredicate(pathcontainsT, [varP, varR, varK])
    nextRule.addBodyPredicate(relationsT, [varX, varR, varX1])
    nextRule.addHeadPredicate(existsPT, [varX1, varP, varT, varKp1])
    '''
        (iii) relation_chain_holds(T,P,Y) :- existsP(Y,P,T,N) ^ path(P,N).
    '''
    [varY, varP, varT, varN] = getVariables(
        ['Y', 'P', 'T', 'N'],
        [ArgumentType.UNIQUEID, ArgumentType.STRING, ArgumentType.UNIQUEID, ArgumentType.NUMERIC])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)

    nextRule.addBodyPredicate(existsPT, [varY, varP, varT, varN])
    nextRule.addBodyPredicate(pathT, [varP, varN])
    nextRule.addHeadPredicate(relation_chain_holdsT, [varT, varP, varY])

    '''
        (iv) answer(Y,P,T) :- relation_chain_holds(T,P,Y) ^ getObjecttype(Y) == answertype.
    '''
    [varY, varP, varT] = getVariables(
        ['Y', 'P', 'T'],
        [ArgumentType.UNIQUEID, ArgumentType.STRING, ArgumentType.UNIQUEID])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(relation_chain_holdsT, [varT, varP, varY])
    nextRule.addBodyConstraint(getObjectType, ArgumentType.STRING, "EQ", ArgumentType.STRING)
    nextRule.addHeadPredicate(answerT, [varY, varP, varT])

    '''
        (v) relation_exists(R,Y,T) :-
    '''
    [varY, varP, varR, varT] = getVariables(
        ['Y', 'P', 'R', 'T'],
        [ArgumentType.UNIQUEID, ArgumentType.STRING, ArgumentType.STRING, ArgumentType.UNIQUEID])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(pathcontainsT, [varP, varR])
    nextRule.addBodyPredicate(answerT, [varY, varP, varT])
    nextRule.addHeadPredicate(relation_existsT, [varR, varY, varT])

    '''
        (vi) ent_exists(X1,Y,T) :--
    '''
    [varX, varX1, varY, varP, varR, varT] = getVariables(
        ['X', 'X1', 'Y', 'P', 'R', 'T'],
        [ArgumentType.UNIQUEID, ArgumentType.UNIQUEID, ArgumentType.UNIQUEID,
         ArgumentType.STRING, ArgumentType.STRING, ArgumentType.UNIQUEID])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(existsT, [varX])
    nextRule.addBodyPredicate(pathcontainsT, [varP, varR])
    nextRule.addBodyPredicate(answerT, [varY, varP, varT])
    nextRule.addBodyPredicate(relationsT, [varX, varR, varX1])
    nextRule.addHeadPredicate(ent_existsT, [varX1, varY, varT])

    '''
        (vi) pair_exists(R,X1,Y,T) :-
    '''
    [varX, varX1, varY, varP, varR, varT] = getVariables(
        ['X', 'X1', 'Y', 'P', 'R', 'T'],
        [ArgumentType.UNIQUEID, ArgumentType.UNIQUEID, ArgumentType.UNIQUEID,
         ArgumentType.STRING, ArgumentType.STRING, ArgumentType.UNIQUEID])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(existsT, [varX])
    nextRule.addBodyPredicate(pathcontainsT, [varP, varR])
    nextRule.addBodyPredicate(answerT, [varY, varP, varT])
    nextRule.addBodyPredicate(relationsT, [varX, varR, varX1])
    nextRule.addHeadPredicate(pair_existsT, [varR, varX1, varY, varT])

    '''
        (vii) not_final_answer(Y,T) :-
    '''
    [varY, varR, varT] = getVariables( ['Y', 'R', 'T'],
        [ArgumentType.UNIQUEID, ArgumentType.STRING,
         ArgumentType.UNIQUEID])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(condition_relT, [varR])
    nextRule.addBodyPredicate(relation_existsT, [varR, varY, varT], 'neg')
    nextRule.addHeadPredicate(not_final_answerT, [varY, varT])

    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(condition_pairT, [varR, varX])
    nextRule.addBodyPredicate(pair_existsT, [varR, varX, varY, varT], 'neg')
    nextRule.addHeadPredicate(not_final_answerT, [varY, varT])

    '''
        (viii) final_answer(Y) :-
    '''
    [varY, varP, varT] = getVariables(
        ['Y', 'P', 'T'],
        [ArgumentType.UNIQUEID, ArgumentType.STRING, ArgumentType.UNIQUEID])
    nextRule = ruleBase.addRuleTemplate(True, 10.0)
    nextRule.addBodyPredicate(answerT, [varY, varP, varT])
    nextRule.addBodyPredicate(not_final_answerT, [varY, varT], 'neg')
    nextRule.addHeadPredicate(final_answerT, [varY])

    '''
        4. associate predicates to domains
        For evidence, get all predicates from files.
            e.g. topic, condition, path  etc.
            e.g. it will extend and set the domain again
    '''
    allTemplates = {topicT, conditionT, pathT, pathcontainsT, condition_relT, condition_pairT,
                    relationsT, existsPT, relation_chain_holdsT, answerT, relation_existsT, ent_existsT, pair_existsT,
                    not_final_answerT, final_answerT}

    for qIndex in range(0, 1):
        qIndex = 0
        dir = 'data/domain/trn-q' + str(qIndex) + '/'
        '''
        3.i) populate these domains from different files.
            topicIDDomain, conditionIDDomain, pathInfo, pathRelations
            conditionRelations, conditionPairs, allFBRelations
        '''
        domainDict = {}
        for template in allTemplates:
            if template.isEvidence:
                domainDict[template.name] = DomainTuple(template.name)
                [dataTuples, truthvalues] = loadFromTSVData(dir + template.name + ".txt", template.arity)
                domainDict[template.name].setData(dataTuples, truthvalues)
                template.setDomain(domainDict[template.name])
        '''
        3. ii) --do--
            entityIDDomain, pathStringsDomain, relationStringsDomain
        '''
        entityIDDomain = DomainTuple('entityID')
        entityIDDomain.setData(loadFromTSVData(dir + entityIDDomain.name + ".txt"))
        pathStringsDomain = DomainTuple('pathStrings')
        pathStringsDomain.setData(loadFromTSVData(dir + pathStringsDomain.name + ".txt"))
        relationStringsDomain = DomainTuple('relationStrings')
        relationStringsDomain.setData(loadFromTSVData(dir + relationStringsDomain.name + ".txt"))

        nameToTemplateMap = {}
        for template in allTemplates:
            nameToTemplateMap[template.name] = template

        '''
            5. associate variables to super-domains for fall-back
        '''
        variableSuperDomainMap = {'X': entityIDDomain, 'X1': entityIDDomain, 'Y': entityIDDomain,
                                  'P': pathStringsDomain, 'R': relationStringsDomain}

        inferredGurobiModel = pslground.infer(ruleBase, variableSuperDomainMap, nameToTemplateMap)
