from pslplus.core import pslground
import numpy as np
import logging

"""
Infers based on the rules and detected groundtruth.
"""

class Inference(object):
    def __init__(self, ruleBase, trainingDomainMap, predDB, nameToTemplateMap, averageSteps=True):
        self.ruleBase = ruleBase
        self.trainingDomainMap = trainingDomainMap
        self.predicatesDB = predDB

        self.nameToTemplateMap = nameToTemplateMap

        self.numSteps = 100 # some constant
        self.stepSize = 0.1 # STEP_SIZE_DEFAULT = 1.0
        self.scheduleStepSize = True
        self.averageSteps = averageSteps

        self.l2Regularization = 0.0
        self.l1Regularization = 0.0

    def infer(self, s_cand=20.0, s_ans=20.0):
        [headVariablesDict, summarytablesAlreadyCreated] = pslground.inferHeadVariables(
            self.ruleBase, self.trainingDomainMap, self.predicatesDB,
            self.nameToTemplateMap, S_CAND=s_cand)
        for i in range(0, len(self.ruleBase.ruleTemplates)):
            ruleT = self.ruleBase.ruleTemplates[i]
            ruleT.cleanupGroundedRules()
        print "Inference done."
        return [headVariablesDict, summarytablesAlreadyCreated]

