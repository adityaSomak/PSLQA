

class PredicatesDB:
    def __init__(self, predicatesRuleDBconn, predicatesCursorDB, tables, evidencePredicateTemplates):
        self.predicatesRuleDBconn = predicatesRuleDBconn
        self.predicatesCursorDB = predicatesCursorDB
        self.tableNames = tables
        self.nameToPredTempateMap = evidencePredicateTemplates

    def insertHeadTemplateTables(self,combinedHeadPredicateMap):
        for templateName in combinedHeadPredicateMap:
            datarows = list(combinedHeadPredicateMap[templateName])
            print templateName + " Table Creating with rows... " + str(len(datarows))
            arity = len(datarows[0].split(","))
            self.createTable(arity, templateName)
            self.insertIntoTable(arity, templateName, datarows)
        self.predicatesRuleDBconn.commit()

    def createTable(self,numArgs, predName):
        t = (predName)
        if numArgs == 1:
            self.predicatesCursorDB.execute("CREATE TABLE if not exists {} (ARG1 text, value real)".format(predName))
        elif numArgs == 2:
            self.predicatesCursorDB.execute("CREATE TABLE if not exists {} (ARG1 text, ARG2 text, value real)".format(predName))
        elif numArgs == 3:
            self.predicatesCursorDB.execute("CREATE TABLE if not exists {} (ARG1 text, ARG2 text, "
                                            "ARG3 text, value real)".format(predName))
        elif numArgs == 4:
            self.predicatesCursorDB.execute("CREATE TABLE if not exists {} (ARG1 text, ARG2 text, ARG3 text, "
                                            "ARG4 text, value real)".format(predName))

    def insertIntoTable(self, numArgs, tName, csvdata):
        values = []
        for i, joinedL in enumerate(csvdata):
            l = joinedL.split(",")
            l.append(-1.0)
            values.append(tuple(l))

        self.insertTable(numArgs, tName, values)

    def insertTable(self,numArgs, predName, values):
        if numArgs == 1:
            self.predicatesCursorDB.executemany("INSERT INTO  {} values (?,?)".format(predName), values)
        elif numArgs == 2:
            self.predicatesCursorDB.executemany("INSERT INTO  {} values (?,?,?)".format(predName), values)
        elif numArgs == 3:
            self.predicatesCursorDB.executemany("INSERT INTO  {} values (?,?,?,?)".format(predName), values)
        elif numArgs == 4:
            self.predicatesCursorDB.executemany("INSERT INTO  {} values (?,?,?,?,?)".format(predName), values)