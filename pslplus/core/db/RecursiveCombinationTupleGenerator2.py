from pslplus.core.pslcore import Constant

class RecursiveCombinationTupleGeneratorFast(object):

    def __init__(self, predicatesDB, pNameToVarNamesMap, pNameToVariablesMap, summarytablesAlreadyCreated):
        self.predicatesDB = predicatesDB
        # Keys are  index-appended predicate-names
        # Example:
        #      Friend(X,Y) ^ Friend(Y,Z) ^ smokes(X) --> smokes(Z)
        # nameToVariablesMap =  {Friend_0: ['X','Y'], Friend_1: ['Y','Z'], smokes: ['X']}
        self.nameToVariablesMap = pNameToVarNamesMap

        allIndexedPredicateNames = list(pNameToVarNamesMap.keys())

        summarytableName = allIndexedPredicateNames[0][:allIndexedPredicateNames[0].rindex("_")]
        summaryTableVariables = pNameToVarNamesMap[allIndexedPredicateNames[0]]
        sqlite_columnnames_summaryTable = self.getSQLiteColumnNames(summarytableName)

        for i in range(1,len(allIndexedPredicateNames)):
            secondTableName = allIndexedPredicateNames[i][:allIndexedPredicateNames[i].rindex("_")]
            secondTableVariableNames = pNameToVarNamesMap[allIndexedPredicateNames[i]]
            sqlite_columnnames_secondTable = self.getSQLiteColumnNames(secondTableName)
            [columns,names] = getIntersectingColumns(
                summarytableName, summaryTableVariables,secondTableName, secondTableVariableNames,
                sqlite_columnnames_summaryTable, sqlite_columnnames_secondTable, i)
            [condition, values] = getConstantColumns(
                secondTableName, secondTableVariableNames, pNameToVariablesMap[allIndexedPredicateNames[i]])
            print "Iteration: "+ str(i)
            newTableName = summarytableName+"_"+secondTableName
            prefixString = "create table if not exists {} as ".format(newTableName)
            if newTableName in summarytablesAlreadyCreated:
                prefixString = "insert into {} ".format(newTableName)
            if columns is None:
                #self.predicatesDB.predicatesCursorDB.execute("create table if not exists {}".format(newTableName))
                if condition is None:
                    querystring = prefixString +\
                                  " select * from "+ summarytableName+\
                                  " CROSS JOIN " + secondTableName
                    self.predicatesDB.predicatesCursorDB.execute(querystring)
                else:
                    querystring = prefixString +\
                                  " select * from " + summarytableName + \
                                  " CROSS JOIN " + secondTableName + " where "+ condition
                    self.predicatesDB.predicatesCursorDB.execute(querystring, values)
                print querystring
                if i == 1:
                    summaryTableVariables.append(summarytableName+"_value")
                summaryTableVariables.extend(secondTableVariableNames)
                summaryTableVariables.append(secondTableName + "_value")
            else:
                if condition is None:
                    querystring = prefixString + \
                                  " select * from " + summarytableName + \
                                  " INNER JOIN " + secondTableName + " ON "+ columns
                    self.predicatesDB.predicatesCursorDB.execute(querystring)
                else:
                    querystring = prefixString + \
                                  " select * from " + summarytableName + \
                                  " INNER JOIN " + secondTableName + " ON " + columns + " where " + condition
                    self.predicatesDB.predicatesCursorDB.execute(querystring,values)
                print querystring
                summaryTableVariables = names
            summarytablesAlreadyCreated.add(newTableName)
            self.predicatesDB.predicatesRuleDBconn.commit()
            summarytableName = newTableName
            sqlite_columnnames_summaryTable = self.getSQLiteColumnNames(summarytableName)
            print summaryTableVariables
        self.summarytableName = summarytableName
        self.variableNames = summaryTableVariables

    def getResultsFromSummaryTable(self):
        self.predicatesDB.predicatesCursorDB.execute("select * from {}".format(self.summarytableName))
        resultslist = []
        for row in self.predicatesDB.predicatesCursorDB:
            resultslist.append(row)
        print "Number of combinations:" + str(len(resultslist))
        return iter(resultslist)

    def getSQLiteColumnNames(self, summarytableName):
        self.predicatesDB.predicatesCursorDB.execute("select * from {}".format(summarytableName))
        names = list(map(lambda x: x[0], self.predicatesDB.predicatesCursorDB.description))
        print summarytableName + "::"+ ",".join(names)
        return names


def getConstantColumns(secondTableName, secondTableVariableNames, secondTableVariables):
    conditionslist = []
    valueList = []
    for i, name in enumerate(secondTableVariableNames):
        if isinstance(secondTableVariables[i],Constant):
            conditionslist.append(secondTableName + ".ARG" + str(i + 1) + "= ?")
            valueList.append(name)
    if len(conditionslist) > 0:
        return [" and ".join(conditionslist), tuple(valueList)]
    return [None, None]


def getIntersectingColumns(summaryTableName, summaryvariableNames, secondTableName, secondTableVariableNames,
                           sqlite_columnnames_summaryTable, sqlite_columnnames_secondTable, iter):
    list = []
    nameList = []
    for j,name in enumerate(summaryvariableNames):
        try:
            i = secondTableVariableNames.index(name)
            list.append(summaryTableName + "."+ sqlite_columnnames_summaryTable[j] + "=" +
                        secondTableName + "."+ sqlite_columnnames_secondTable[i])
            #list.append(summaryTableName + ".ARG" + str(j + 1) + "=" + secondTableName + ".ARG" + str(i + 1))
        except ValueError:
            pass
        nameList.append(name)
    if iter == 1:
        nameList.append(summaryTableName+"_value")
    for i, name in enumerate(secondTableVariableNames):
        nameList.append(name)
    nameList.append(secondTableName + "_value")
    if len(list) > 0:
        return [" and ".join(list),nameList]
    return [None,None]
