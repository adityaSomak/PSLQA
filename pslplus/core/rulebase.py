from pslcore import *
import externalfunctions


class RuleBase(object):
    def __init__(self):
        self.ruleTemplates =[]
        self.pTemplateMap = PredicateTemplateMap()
        self.currentRuleIndex = 0

    def addPredicateTemplate(self, name, types):
        self.pTemplateMap.addTemplate(name,types)

    def addRuleTemplates(self, avgconjrule, weight):
        ruleT = RuleTemplate(avgconjrule, weight, self.pTemplateMap, self.currentRuleIndex)
        self.currentRuleIndex += 1
        self.ruleTemplates.append(ruleT)
        return ruleT

    def getTemplateByIndex(self, index):
        return self.ruleTemplates[index]

    def printRuleBase(self):
        for ruleT in self.ruleTemplates:
            print ruleT


class RuleTemplate(object):
    """
    Class for templating Rules.
    Example way to Declare:
     5.0, smokes(B) :: friends(A,B) ^ smokes(A)
     3.0, smokes(B) :: friends(A,B) ^ smokes(A), avgconj
     1.0, smokes(B) or smokes(C) :: friends(A,B) ^ smokes(A) ^ friends(A,C)
     smokes(B) :: friends(A,B) ^ smokes(A)
     10.0, smokes(B) :: parent(A,B) ^ not smokes(A)

    Rule-Body can have constraints too of the form that can be
     templated by ConstraintTemplate
    Example Usage:
    >> pTemplateMap = PredicateTemplateMap();
    >> varA = Variable('A', ArgumentType.STRING);
    >> varB = Variable('B', ArgumentType.STRING);
    >> friendsT = PredicateTemplate('friends', [ArgumentType.STRING, ArgumentType.String]);
    >> smokesT = PredicateTemplate('smokes', [ArgumentType.STRING]);
    >> rule1 = RuleTemplate(True, w, pTemplateMap);
    >> rule1.addBodyPredicate(friendsT, [varA,varB]);   // friends(A,B)
    >> rule1.addBodyPredicate(smokesT, [varA]);         // smokes(A)
    >> rule1.addHeadPredicate(smokesT, [varB]);         // smokes(B)
    >> rule2 = RuleTemplate(True, w, pTemplateMap);

    Assumption:
       Actual Grounded Rule Weight  =  W_gr = alpha1_rt * W_rt + alpha2_rt * W_sim.
       W_sim = weight based on similarities.
       (alpha1_rt, alpha2_rt) = scale for the RT weight and GR weight.
    """
    def __init__(self, avgconjrule, weight, pTemplateMap, currentRuleIndex):
        self.ID = currentRuleIndex
        self.avgconjrule = avgconjrule
        self.isconstraint =  (weight=='inf')
        self.pTemplateMap = pTemplateMap

        self.bodypTemplates = OrderedDict()  #pred-name --> [variables_1, variables_2..]
        self.bodypPolarity = OrderedDict()   #pred-name --> [polarities_1, polarities_2...]
        self.bodypExternalFunction = OrderedDict()
        self.headpTemplates = OrderedDict()  #pred-name --> variables
        self.headpPolarity = OrderedDict()
        self.bodyconstraints = []
        self.varTypeMap =  VariableTypeMap()
        self.groundedRules = []
        self.allTemplates = None
        self.templateWeight = 1.0
        if weight != 'inf':
            self.templateWeight = weight
        self.alpha1 = 1.0
        self.alpha2 = 4.0
        # Hardcoded Wts: alpha1 = 1.0, alpha2 = 4.0
        # Hardcoded: FinalWeight: 1.0 * self.templateWeight + 4.0 * 1.0

    def printWeights(self):
        weights = "templateWeight:"+str(self.templateWeight)+"; alphas: ["+str(self.alpha1)+", "+str(self.alpha2)+"]"
        print self.ID+": "+ weights

    def getFinalWeight(self, groundedRuleSimilarity):
        #return self.templateWeight * groundedRuleSimilarity
        return self.alpha1 * self.templateWeight + self.alpha2 * groundedRuleSimilarity

    def getAllTemplates(self):
        if self.allTemplates is None:
            self.allTemplates = OrderedDict()
            self.allTemplates.update(self.bodypTemplates)
            self.allTemplates.update(self.headpTemplates)
        return self.allTemplates

    def getPolarity(self, tName, isBody = True):
        if isBody:
            return self.bodypPolarity[tName]
        return self.headpPolarity[tName]

    def getVariablesOfPredicate(self, templateName):
        if templateName in self.bodypTemplates:
            return self.bodypTemplates[templateName]
        return self.headpTemplates[templateName]

    def addBodyPredicate(self, predTemplate, variables, isNeg = 'pos'):
        if predTemplate.name in self.bodypTemplates:
            self.bodypTemplates[predTemplate.name].append(variables)
            self.bodypPolarity[predTemplate.name].append((isNeg == 'pos'))
        else:
            self.bodypTemplates[predTemplate.name] = [variables]
            self.bodypPolarity[predTemplate.name] = [(isNeg == 'pos')]
        if predTemplate.name.startswith("Fn_"):
            self.bodypExternalFunction[predTemplate.name] = externalfunctions.allFunctions[predTemplate.name[3:]]
        types = [var.type for var in variables]
        self.pTemplateMap.addTemplate(predTemplate.name,types)
        for var in variables:
            self.varTypeMap.addVariable(var)

    def addHeadPredicate(self, predTemplate, variables, isNeg = 'pos'):
        self.headpTemplates[predTemplate.name] = variables
        self.headpPolarity[predTemplate.name] = (isNeg == 'pos')
        types = [var.type for var in variables]
        self.pTemplateMap.addTemplate(predTemplate.name,types)
        for var in variables:
            self.varTypeMap.addVariable(var,True)

    '''
      From a grounded body predicate value collection get the predicate values
       for head predicate:
       smokes(A) :: friends(A,B) ^ smokes(B)
       friends(john,eddy), smokes(eddy)
       In head, we get smokes(john)
    '''
    def getHeadPredicateTuple(self, groundedbodyPredicateMap, headpT_Name):
        variablesInheadp = self.headpTemplates[headpT_Name]
        variableValues = {}
        for bodypTemplate in self.bodypTemplates:
            valueTupleList = groundedbodyPredicateMap[bodypTemplate]
            for i in range(0, len(self.bodypTemplates[bodypTemplate])):
                values = valueTupleList[i]
                variablesInbodyp = self.bodypTemplates[bodypTemplate][i]
                j= 0
                for variable in variablesInbodyp:
                    variableValues[variable.name] = values[j]
                    j += 1
        headpredicatevalues = []
        for variable in variablesInheadp:
            headpredicatevalues.append(variableValues[variable.name])
        return headpredicatevalues

    def addBodyConstraint(self, constrName, types, relation=None, constantType=None):
        self.bodyconstraints.append(ConstraintTemplate(constrName, types, relation, constantType))

    def addGroundedRule(self,grRule):
        self.groundedRules.append(grRule)

    def getGroundedRules(self):
        return self.groundedRules

    def cleanupGroundedRules(self):
        self.groundedRules = []

    def __str__(self):
        finalStr = str(self.templateWeight)+"*"+str(self.alpha1)+"+grw*"+str(self.alpha2)+", "
        i = 0
        for headPName,variables in self.headpTemplates.iteritems():
            if i > 0:
                finalStr += " V "
            finalStr += getString(headPName, variables)
            i+= 1
        finalStr += "<--"
        i=0
        for bodyPName,variablesLists in self.bodypTemplates.iteritems():
            for variables in variablesLists:
                if i > 0:
                    finalStr += " ^ "
                finalStr += getString(bodyPName, variables)
                i += 1
        return finalStr

def getString(predicateName, variables):
    names = [var.name for var in variables]
    return predicateName + "(" + ",".join(names) + ")"