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
    elif numArgs == 5:
        cursorDB.execute("CREATE TABLE {} (ARG1 text, ARG2 text, ARG3 text, ARG4 text, ARG5 text, value real)".format(predName))

def insertTable(numArgs, predName, values, cursorDB):
    if numArgs == 1:
        cursorDB.executemany("INSERT INTO  {} values (?,?)".format(predName),values)
    elif numArgs == 2:
        cursorDB.executemany("INSERT INTO  {} values (?,?,?)".format(predName),values)
    elif numArgs == 3:
        cursorDB.executemany("INSERT INTO  {} values (?,?,?,?)".format(predName),values)
    elif numArgs == 4:
        cursorDB.executemany("INSERT INTO  {} values (?,?,?,?,?)".format(predName), values)
    elif numArgs == 5:
        cursorDB.executemany("INSERT INTO  {} values (?,?,?,?,?,?)".format(predName), values)
    elif numArgs == 6:
        cursorDB.executemany("INSERT INTO  {} values (?,?,?,?,?,?,?)".format(predName), values)

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


def fillTrainingDomainMap(trainingDomainMap, qidFile, predicate_to_count="default"):
    S_estimate = 0.0
    with open(qidFile, 'r') as f:

        for line in f:
            line = line.replace("\n", "")
            if line == "" or line.startswith("#"):
                continue
            tokens = line.split("\t")
            templatename = tokens[0].strip()

            if templatename == predicate_to_count:
                S_estimate += 1.0

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

    if predicate_to_count == "default":
        return [20.0, 20.0]
    else:
        return [S_estimate * 2.0, S_estimate * 2.0]


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
    pslCodeFile = argsdict['pslcode'] # "psl_rules.txt"
    data_directory = argsdict['datadir'] # "data/"
    startFrom = argsdict['startFrom']
    predicate_to_count = argsdict['mention']
    [ruleBase,evidencePredicateTemplates] = pslcodeparser.parsePSLTemplates(pslCodeFile)
    # ruleBase.printRuleBase()

    # dataDirectory += '/'

    if argsdict['option'] == 'infer':
        if os.path.isfile(data_directory):
            list_of_input_files = [data_directory]
            data_directory = data_directory[:data_directory.rindex("/")]
        else:
            list_of_input_files = os.listdir(data_directory)
        outputDir = data_directory+"/"+"psl"
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        instance_count = 0
        for instanceFile in list_of_input_files:
            trainingDomainMap = {"head": {}}
            print "######processing: "+str(instance_count)+":"+ instanceFile
            instanceFile = data_directory + "/" + instanceFile
            if os.path.isdir(instanceFile):
                continue
            instance_count += 1
            if instance_count < startFrom:
                continue
            if os.path.exists(outputDir + "/" + instanceFile[instanceFile.rindex("/")+1:]):
                continue
            if instance_count > startFrom+30000:
                break

            databaseconn = sqlite3.connect('pslgeneric' + str(startFrom) + '.db')
            cursorDB = databaseconn.cursor()
            s_cand, s_ans = fillTrainingDomainMap(trainingDomainMap, instanceFile,
                                                  predicate_to_count=predicate_to_count)

            try:
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
                [headVariablesDict, summarytablesAlreadyCreated] = inference.infer(s_cand=s_cand)
                sortedHVariables = sorted(headVariablesDict.items(), key=operator.itemgetter(1),reverse=True)
                with open(outputDir + "/" + instanceFile[instanceFile.rindex("/")+1:],'w') as opFile:
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
            os.system("rm {}".format('pslgeneric'+str(startFrom)+'.db'))
    print "Thread finished"

