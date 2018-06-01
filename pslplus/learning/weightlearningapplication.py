from pslplus.core import pslground
import numpy as np
import math
import logging

"""
Learns new weights for the ruleTemplates in a RuleBase using
the voted perceptron algorithm.

The weight-learning objective is to maximize the likelihood
according to the distribution:
   p(X) = 1 / Z(w)   *   exp{-sum[w * f(X)]}

    where X is the set of RandomVariables, f(X) the incompatibility
of each GroundedRule, w is the weight of that GroundedRule, and Z(w)
is a normalization factor.

  The voted perceptron algorithm starts at the current weights and
  at each step computes the gradient of the objective, takes that step
  multiplied by a step size (possibly truncated to stay in the region of
  feasible weights), and saves the new weights. The components of the
  gradient are each divided by the number of GroundedRules
  from that ruleTemplate. The learned weights are the averages of the
  saved weights.

  For the gradient of the objective, the expected total incompatibility
  is computed by `~core.pslGround.computeExpectedIncomp()`.
"""

class WeightLearning(object):
    def __init__(self, ruleBase, trainingDomainMap, nameToTemplateMap, averageSteps=True):
        self.ruleBase = ruleBase
        self.trainingDomainMap = trainingDomainMap
        self.nameToTemplateMap = nameToTemplateMap

        self.numSteps = 100 # some constant
        self.stepSize = 0.1 # STEP_SIZE_DEFAULT = 1.0
        self.scheduleStepSize = True
        self.averageSteps = averageSteps

        self.l2Regularization = 0.0
        self.l1Regularization = 0.0

    def learn(self):
        #self.initGroundModel()
        self.avgWeights = np.zeros((len(self.ruleBase.ruleTemplates)))
        self.doLearn()

    def initGroundModel(self):
        pass

    def update(self, predDB):
        scalingFactor = []

        [truthIncompatibility, numGroundings, grTruthIncompatibilities] = pslground.\
            computeObservedIncomp(self.ruleBase, self.trainingDomainMap,
                                  self.nameToTemplateMap, predDB, True)
        print "Observed Incompatibility: "+str(truthIncompatibility)+"; Groundings:"+str(numGroundings)

        for step in range(0,self.numSteps):

            logging.info('*** Iteration {%s} ***', str(step))
            # Computes the expected total incompatibility for each CompatibilityKernel
            expectedIncompatibility, numInferenceGroundings, grExpectedIncompatibilities = pslground.\
                computeExpectedIncomp(self.ruleBase, self.trainingDomainMap,
                self.nameToTemplateMap, step)
            print "Expected Incompatibility: "+str(expectedIncompatibility)+"; Groundings:"+str(numInferenceGroundings)

            scalingFactor = self.computeScalingFactor(numGroundings)
            #loss = self.computeLoss(expectedIncompatibility, truthIncompatibility)

            for i in range(0,len(self.ruleBase.ruleTemplates)):
                ruleT = self.ruleBase.ruleTemplates[i]

                weight = ruleT.templateWeight
                # TODO: Change gradient step
                currentStep_w = ((expectedIncompatibility[i] - truthIncompatibility[i]) * ruleT.alpha1
                               - self.l2Regularization * weight -
                               self.l1Regularization) / scalingFactor[i]
                currentStep_w *= self.getStepSize(step)
                weight += currentStep_w
                weight = max(weight, 1.0)
                self.avgWeights[i] += weight
                ruleT.templateWeight = weight
                ruleT.cleanupGroundedRules()
                print ruleT

    def finishLearning(self):
        if self.averageSteps:
            for i in range(0,len(self.ruleBase.ruleTemplates)):
                avgWt = self.avgWeights[i]/self.numSteps
                self.ruleBase.ruleTemplates[i].templateWeight = avgWt
        logging.info("Learning done.")
        for ruleT in self.ruleBase.ruleTemplates:
            print ruleT

    def computeLoss(self, expectedIncompatibility, truthIncompatibility):
        loss =0
        for i in range(0,len(self.ruleBase.ruleTemplates)):
            loss += self.ruleBase.getTemplateByIndex(i).weight * \
                    (truthIncompatibility[i] - expectedIncompatibility[i])
        return loss

    def computeScalingFactor(self, numGroundings):
        factor = []
        for i in range(0, len(numGroundings)):
            if numGroundings[i] > 0:
                factor.append(numGroundings[i])
            else:
                factor.append(1.0)
        return factor

    def computeRegularizer(self):
        l1 = 0
        l2 = 0
        for i in range(0, len(self.ruleBase.ruleTemplates)):
            ruleT = self.ruleBase.ruleTemplates[i]
            l2 += math.pow(ruleT.templateWeight, 2)
            l1 += math.abs(ruleT.templateWeight)
        return 0.5 * self.l2Regularization * l2 + self.l1Regularization * l1

    def cleanUpGroundModel(self):
        raise NotImplementedError

    def getStepSize(self,iter):
        if self.scheduleStepSize:
            return self.stepSize /(iter + 1)
        else:
            return self.stepSize
