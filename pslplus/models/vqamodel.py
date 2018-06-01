from pslplus.learning import weightlearningapplication
from pslplus.infer import inferenceapplication1
from pslplus.core.pslcore import *
from pslplus.core.domain import *
from pslplus.parser import pslcodeparser
import argparse, sys, os, operator
from pslplus.core.db import predicatesdb
import sqlite3
from pslplus.core.similarity import W2VPredicateSimilarity as w2v
import traceback

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
        if varTypes[i] == ArgumentType.NUMERIC and optionalValues is not None and optionalValues[i] is not None:
            var = Variable(varNames[i], varTypes[i], optionalValues[i])
        else:
            var = Variable(varNames[i], varTypes[i])
        variables.append(var)
    return variables

def createTable(numArgs, predName, cursorDB):
    t = (predName)
    if numArgs == 1:
        cursorDB.execute("CREATE TABLE {} (ARG1 text, value real)".format(predName))
    elif numArgs == 2:
        cursorDB.execute("CREATE TABLE {} (ARG1 text, ARG2 text, value real)".format(predName))
    elif numArgs == 3:
        cursorDB.execute("CREATE TABLE {} (ARG1 text, ARG2 text, ARG3 text, value real)".format(predName))

def insertTable(numArgs, predName, values, cursorDB):
    if numArgs == 1:
        cursorDB.executemany("INSERT INTO  {} values (?,?)".format(predName),values)
    elif numArgs == 2:
        cursorDB.executemany("INSERT INTO  {} values (?,?,?)".format(predName),values)
    elif numArgs == 3:
        cursorDB.executemany("INSERT INTO  {} values (?,?,?,?)".format(predName),values)

def createAllTables(cursorDB, trainingDomainMap, evidencePredicateTemplates):
    tables = []
    for tName in evidencePredicateTemplates:
        if not tName.startswith("Fn_"):
            predTemplate = evidencePredicateTemplates[tName]
            if tName in trainingDomainMap and (trainingDomainMap[tName][0] is not None) and \
                            len(trainingDomainMap[tName][0]) > 0:
                createTable(predTemplate.arity, predTemplate.name, cursorDB)
                tables.append(predTemplate.name)
    return  tables

def insertIntoTable(cursorDB, numArgs, tName, csvdata):
    values = []
    for i,cdata in enumerate(csvdata[0]):
        l = []
        if tName == "word" or numArgs == 2:
            if len(cdata) > 2:
                print cdata
            l.extend(cdata.replace(","," "))
        else:
            l.extend(cdata.split(","))
        l.append(csvdata[1][i])
        values.append(tuple(l))
    insertTable(numArgs, tName, values, cursorDB)

def reducePossibleAnswers(trainingDomainMap, vqaPriorDirectory, question, answerPriorByTypeDict, qid, filteredAnswers):
    if vqaPriorDirectory is not None:
        datatuples = []
        truthValues = []
        with open(vqaPriorDirectory+"/ques"+qid+".txt",'r') as priorAnswers:
            for line in priorAnswers:
                tokens = line.split("\t")
                if filteredAnswers is not None:
                    if tokens[1].replace("\n","") in filteredAnswers:
                        truthValues.append(float(tokens[0]))
                        datatuples.append(tokens[1].replace("\n", ""))
                else:
                    truthValues.append(float(tokens[0]))
                    datatuples.append(tokens[1].replace("\n",""))
        minValue = min(truthValues)
        maxValue = max(truthValues)
        newtruthValues = [(x-minValue)/(maxValue-minValue) for x in truthValues]
        trainingDomainMap["word"] = (datatuples, newtruthValues)
        print datatuples
        return

    if answerPriorByTypeDict is not None:
        qWords = question.lower().split(" ")
        answersDict = None
        if " ".join(qWords[:4]) in answerPriorByTypeDict:
            answersDict = answerPriorByTypeDict[" ".join(qWords[:4])]
        elif " ".join(qWords[:3]) in answerPriorByTypeDict:
            answersDict = answerPriorByTypeDict[" ".join(qWords[:3])]
        elif " ".join(qWords[:2]) in answerPriorByTypeDict:
            answersDict = answerPriorByTypeDict[" ".join(qWords[:2])]
        elif " ".join(qWords[:1]) in answerPriorByTypeDict:
            answersDict = answerPriorByTypeDict[" ".join(qWords[:1])]
        elif qWords[0] in answerPriorByTypeDict:
            answersDict = answerPriorByTypeDict[qWords[0]]
        if answersDict is not None:
            datatuples = []
            truthValues = []
            i=0
            for answer in answersDict:
                datatuples.append(str(answer.encode('utf-8')))
                truthValues.append(float(answersDict[answer]))
                if i > 100:
                    break
                i+=1
            trainingDomainMap["word"] = (datatuples, truthValues)
            print datatuples
            return

    w2v.loadW2VModel()
    possibleWords = trainingDomainMap["word"][0]
    wordsInQuestion = set()
    tuplesInQuestion = trainingDomainMap["has_q"][0]
    for tQ in tuplesInQuestion:
        triplet = tQ.split(",")
        for phrase in triplet:
            if phrase != "?x":
                wordsInQuestion.update(phrase.split(" "))
            #wordsInQuestion.update(words[2].split(" "))
    wordsInQuestion = wordsInQuestion.difference({"on","in","the"})
    finalWordsInQ = []
    for word in wordsInQuestion:
        try:
            vec = w2v.word2vec_model[word]
            finalWordsInQ.append(word)
        except KeyError:
            continue
    tuples = []
    for word in possibleWords:
        sim = w2v.similarityToAlistofWords(word.split(" "), finalWordsInQ)
        if sim is not None:
            tuples.append((sim,word))
    tuples = sorted(tuples, key=lambda x: abs(x[0]), reverse=True)
    datatuples = map(lambda x: x[1],tuples[:200])
    truthvalues = trainingDomainMap["word"][1][:200]
    trainingDomainMap["word"] = (datatuples, truthvalues)
    #print tuples[:200]
    print datatuples

def getAnswersByType(question,answersByType):
    question = question.lower()
    colorQs = {'what color', 'what is the color of'}
    for colorQ in colorQs:
        if question.startswith(colorQ):
            return answersByType['color']
    locQs = {'where'}
    for locQ in locQs:
        if question.startswith(locQ):
            answers = answersByType['location']
            answers.extend(answersByType['entity'])
            answers.extend(answersByType['animal'])
            return answers
    humanQs = {'who'}
    for humanQ in humanQs:
        if question.startswith(humanQ):
            answers = answersByType['human']
            answers.extend(answersByType['entity'])
            answers.extend(answersByType['animal'])
            return answers
    return None

def fillTrainingDomainMap(trainingDomainMap, qidFile):
    with open(qidFile, 'r') as f:

        for line in f:
            line = line.replace("\n", "")
            if line == "" or line.startswith("#"):
                continue
            tokens = line.split("\t")
            templatename = tokens[0].strip()

            if tokens[0] == "has_story":
                story_args = tokens[1].split(",")
                if "-" not in story_args[0] or "-" not in story_args[2]:
                    continue
            if len(tokens) > 3 and tokens[3] == "head":
                try:
                    trainingDomainMap["head"][templatename][tokens[1]] = float(tokens[2])
                except KeyError:
                    trainingDomainMap["head"][templatename] = {}
                    trainingDomainMap["head"][templatename][tokens[1]] = float(tokens[2])

            if templatename not in trainingDomainMap:
                trValues = []
                datatuples = []
                trainingDomainMap[templatename] = (datatuples, trValues)

            tupleValues = []
            for val in tokens[1].split(","):
                if "-" in val:
                    tupleValues.append(val[:val.rindex("-")])
                else:
                    tupleValues.append(val)
            trainingDomainMap[templatename][0].append(",".join(tupleValues))
            if len(tokens) <= 2:
                trainingDomainMap[templatename][1].append(1.0)
            else:
                trainingDomainMap[templatename][1].append(float(tokens[2]))


def run(argsdict):
    """
      Method is called  to infer or learn using vqa-model.
      This will be later generalized to read any rule-base and dataset.
    """
    #parser = argparse.ArgumentParser()
    #parser.add_argument("pslcode")
    #parser.add_argument("-datadir")
    #parser.add_argument("-option", choices=["learn","infer"])
    #argsdict = vars(parser.parse_args(args))

    #print argsdict
    pslCodeFile = argsdict['pslcode'] # "vqa_psl.txt"
    dataDirectory = argsdict['datadir'] # "data/"
    startFrom = argsdict['startFrom']
    vqaPriorDirectory = argsdict['vqaprior']
    qaData = argsdict['qaData']
    answersByType = argsdict['answersByType']
    answerPriorByTypeDict = argsdict['answerPriorByTypeDict']
    [ruleBase,evidencePredicateTemplates] = pslcodeparser.parsePSLTemplates(pslCodeFile)
    # ruleBase.printRuleBase()

    # dataDirectory += '/'

    if argsdict['option'] == 'learn':
        '''
        Assuming each question is formatted into a psl code.
        Each question also must have a unique id, that will uniquely
        identify predicates from a question
        Say: The file would be listed as
        predicate_name   tuple_values   truth_value
        predicate_name   tuple_values   truth_value <head>
        '''
        trainingDomainMap  = {"head": {}}
        question_count = 0
        wtlearning = weightlearningapplication.WeightLearning(ruleBase, trainingDomainMap, evidencePredicateTemplates)
        for qidFile in os.listdir(dataDirectory):
            trainingDomainMap = {"head": {}}
            print "######processing: " + str(question_count) + ":" + qidFile
            qidFile = dataDirectory + "/" + qidFile
            if os.path.isdir(qidFile):
                continue
            question_count += 1
            if os.path.exists(dataDirectory + "/" + qidFile[qidFile.rindex("/") + 1:]):
                continue
            databaseconn = sqlite3.connect('vqa' + str(startFrom) + '.db')
            cursorDB = databaseconn.cursor()
            fillTrainingDomainMap(trainingDomainMap, qidFile)
            # negativeSampleHeadPredicates(question).
            tables = createAllTables(cursorDB, trainingDomainMap, evidencePredicateTemplates)
            for tName in evidencePredicateTemplates:
                if not tName.startswith("Fn_"):
                    predTemplate = evidencePredicateTemplates[tName]
                    if tName in trainingDomainMap and (trainingDomainMap[tName][0] is not None) and \
                                    len(trainingDomainMap[tName][0]) > 0:
                        domain = Domain(tName, ArgumentType.STRING)
                        insertIntoTable(cursorDB, predTemplate.arity, tName, trainingDomainMap[tName])
                        domain.setData(trainingDomainMap[tName][0], trainingDomainMap[tName][1])
                        predTemplate.setDomain(domain)
                    else:
                        predTemplate.setDomain(None)
            databaseconn.commit()
            predDB = predicatesdb.PredicatesDB(databaseconn, cursorDB, tables, evidencePredicateTemplates)

            wtlearning.update(predDB)
    elif argsdict['option'] == 'infer':
        outputDir = dataDirectory+"/"+"psl"
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        question_count = 0
        for qidFile in os.listdir(dataDirectory):
            trainingDomainMap = {"head": {}}
            print "######processing: "+str(question_count)+":"+ qidFile
            qidFile = dataDirectory + "/" + qidFile
            if os.path.isdir(qidFile):
                continue
            question_count += 1
            if question_count < startFrom:
                continue
            if os.path.exists(outputDir + "/" + qidFile[qidFile.rindex("/")+1:]):
                continue
            if question_count > startFrom+30000:
                break
            qid = qidFile[qidFile.rindex("/") + 1:].replace(".txt", "")
            question = qaData.questionsDict[int(qid)][0].lower()
            if question.startswith("how ") or question.startswith("can you") \
                    or question.startswith("could ") \
                    or question.startswith("has ") \
                    or question.startswith("none of the above "):
                continue
            databaseconn = sqlite3.connect('vqa' + str(startFrom) + '.db')
            cursorDB = databaseconn.cursor()
            fillTrainingDomainMap(trainingDomainMap,qidFile)
            try:
                filteredAnswers= getAnswersByType(question,answersByType)
                reducePossibleAnswers(trainingDomainMap, vqaPriorDirectory,
                                      question, answerPriorByTypeDict,
                                      qid, filteredAnswers)
                tables = createAllTables(cursorDB, trainingDomainMap, evidencePredicateTemplates)
                for tName in evidencePredicateTemplates:
                    if not tName.startswith("Fn_"):
                        predTemplate = evidencePredicateTemplates[tName]
                        if tName in trainingDomainMap and (trainingDomainMap[tName][0] is not None) and \
                                        len(trainingDomainMap[tName][0]) > 0:
                            domain = Domain(tName, ArgumentType.STRING)
                            insertIntoTable(cursorDB, predTemplate.arity, tName, trainingDomainMap[tName])
                            domain.setData(trainingDomainMap[tName][0], trainingDomainMap[tName][1])
                            predTemplate.setDomain(domain)
                        else:
                            predTemplate.setDomain(None)
                databaseconn.commit()
                predDB = predicatesdb.PredicatesDB(databaseconn,cursorDB, tables, evidencePredicateTemplates)
                inference = inferenceapplication1.Inference(
                    ruleBase, trainingDomainMap, predDB, evidencePredicateTemplates)
                [headVariablesDict, summarytablesAlreadyCreated] = inference.infer()
                sortedHVariables = sorted(headVariablesDict.items(), key=operator.itemgetter(1),reverse=True)
                with open(outputDir + "/" + qidFile[qidFile.rindex("/")+1:],'w') as opFile:
                    for pair in sortedHVariables:
                        if pair[1] > 0.0:
                            opFile.write(pair[0]+"\t"+str(pair[1])+"\n")
                    # for key in headVariablesDict:
                    #     opFile.write(key+"\t"+str(headVariablesDict[key])+"\n")
                tables.extend(list(summarytablesAlreadyCreated))
                print "Dropping "+",".join(tables)
                #for table in tables:
                #    databaseconn.execute("drop table {}".format(table))
                for tName in evidencePredicateTemplates:
                    if not tName.startswith("Fn_"):
                        evidencePredicateTemplates[tName].setDomain(None)
            except Exception, e:
                print traceback.format_exc()
            databaseconn.close()
            os.system("rm {}".format('vqa'+str(startFrom)+'.db'))
    print "Thread finished"

