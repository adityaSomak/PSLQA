import argparse
import json
import os
import os.path

from pslplus.models import vqamodel

from ds import datasetprovider as dsp

def writeTestData(qWriter, combinedTriplets, semanticQRelations, nounPairsInQ, possibleAnswers):
    # has_q(.,.,.)
    qStr = "# "
    for nounPair in nounPairsInQ:
        qStr += ",".join(nounPair[:2]) + ";"
    qWriter.write(qStr + "\n")
    for q_relation in semanticQRelations:
        relStr = "has_q\t"+",".join([q_relation.word1,q_relation.relation,
                                  q_relation.word2])+"\t"+str(q_relation.confidence)
        qWriter.write(relStr+"\n")
    # word(.)
    for z_ans in possibleAnswers:
        relStr = "word\t"+ z_ans
        qWriter.write(relStr+"\n")
    # has_story(.,.,.)
    for storyTriplet in combinedTriplets:
        relStr = "has_story\t" + ",".join([storyTriplet.word1, storyTriplet.relation,
                                        storyTriplet.word2])
        qWriter.write(relStr + "\t" + str(storyTriplet.confidence) + "\n")
    #qWriter.close()

def run_stage3(argsdict):
    dataDirectory = argsdict['datadir']
    qaData = argsdict['qaData']
    outputDir = dataDirectory + "/" + "psl"
    opFile = open(argsdict['parentDir']+"/answers_"+argsdict['split']+".txt",'w')
    for aidFile in os.listdir(outputDir):
        with open(outputDir+"/"+aidFile, 'r') as f:
            line = f.readline()
            line = line.replace("\n", "")
            tokens = line.split("\t")
            answer = tokens[0][tokens[0].index("(")+1:-1]
            qid = int(aidFile.replace(".txt",""))
            question = qaData.questionsDict[qid][0]
            op = str(qid)+"\t"+answer+"\t"+tokens[1]+"\t"+question
            print op
            opFile.write(op+"\n")
    opFile.close()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("qaTestDir",help="Testing Directory. Expects images/ as a sub-directory.")
    parser.add_argument("pslDataRootDir",help="PSL Data Root Directory. Expects trn/ as sub-directory.")
    parser.add_argument("answerFile",help="All answers file")
    parser.add_argument("startFrom",help="start from image-index")
    parser.add_argument("-stage",default=1, type=int, help="Stage 1/2/3")
    parser.add_argument("-split",default="test",help="test/dev")
    parser.add_argument("-vqaprior",default="",help="sub-directory under PSL Data Root Directory")
    parser.add_argument("-frequencyprior", default="",help="Frequent answers by type, json file, under PSL Data Root Dir")

    args = parser.parse_args()
    print args

    # 1. Get the Test questions, training images and Dense Captions
    # Questions in: <pslDataRootDir>/test or <pslDataRootDir>/valid
    # Dense Captions in <qaTestDir>/densecap
    print "Loading QA data..."
    [qaData, totalQs] = dsp.getTestQAData(args.__dict__['qaTestDir'], args.__dict__['split'])
    print "Questions loaded..."
    test_imagecaptions_dir = args.__dict__['qaTestDir']+"/densecap"

    answers = dsp.getAllPossibleAnswers(args.__dict__['answerFile'])
    # 3. PSL Input test data folder
    psl_test_data_dir = args.__dict__['pslDataRootDir'] + "/"+ args.__dict__['split']
    if args.__dict__['split'] == 'test':
        psl_test_data_dir = args.__dict__['pslDataRootDir']+"/test"

    vqa_psl_rules = args.__dict__['pslDataRootDir']+"vqa_rules_g.txt"

    startFrom = int(args.__dict__['startFrom'])
    if args.__dict__['stage'] == 2:
        # 5. Iterate over Triplets per question --> Use PSL to answer.
        answersByType = dsp.getAnswersByType(args.__dict__['pslDataRootDir']+"/top1000Answers.tsv")

        vqaPriorDir = None
        answerPriorByTypeDict = None
        if args.__dict__['vqaprior'] != "":
            vqaPriorDir = args.__dict__['pslDataRootDir'] + "/" + args.__dict__['vqaprior']
        elif args.__dict__['frequencyprior'] != "":
            freqPriorJSon = args.__dict__['frequencyprior']
            answerPriorByTypeDict = dsp.getAnswerPriorsByQType(freqPriorJSon)
        options = "" + vqa_psl_rules+" -datadir "+ psl_test_data_dir+ " -option infer"
        argsdict = {'pslcode':vqa_psl_rules, 'datadir':psl_test_data_dir,
                    'vqaprior': vqaPriorDir, 'qaData': qaData,
                    'answerPriorByTypeDict': answerPriorByTypeDict,
                    'answersByType': answersByType,
                    'option':"infer", 'startFrom': startFrom }
        #print argsdict
        vqamodel.run(argsdict)
    else:
        argsdict = {'pslcode': vqa_psl_rules, 'datadir': psl_test_data_dir,
                    'parentDir': args.__dict__['pslDataRootDir'],
                    'qaData': qaData, 'split': args.__dict__['split'], 'startFrom': startFrom}
        run_stage3(argsdict)


if __name__ == "main":
    run()