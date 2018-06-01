#from py2neo import Graph, Path
'''
Populate these domains from different files.
	- topicIDDomain, conditionIDDomain, pathInfo, pathRelations
	conditionRelations, conditionPairs, allFBRelations

	- entityIDDomain, pathStringsDomain, relationStringsDomain
'''
#####################
### topic.txt
### condition.txt
#####################
# prefix = '/windows/drive2/For PhD/KR Lab/FreebaseQA/';
# predictedEntitiesFile = prefix+'Data/STAGG/STAGG-Files/webquestions.examples.train.e2e.top10.filter.tsv';
# entityIDcolumn = 4;
# weightcolumn = 5;
# qIDcolumn = 0;
# dir = prefix+'PSLplus/data/domain/';
# with open(predictedEntitiesFile,'r') as f:
# 	prevId = -1;
# 	fileWrite = None;
# 	for line in f:
# 		tokens = line.split('\t');
# 		qId = int(tokens[qIDcolumn].split("-")[1]);
# 		if prevId == qId:
# 			fileWrite1.write(tokens[entityIDcolumn]+"\t"+tokens[weightcolumn]+"\n");
# 			fileWrite2.write(tokens[entityIDcolumn]+"\t"+tokens[weightcolumn]+"\n");
# 		else:
# 			if fileWrite1:
# 				fileWrite1.close();
# 				fileWrite2.close();
# 			fileWrite1 = open(dir+'trn-q'+str(qId)+'/topic.txt','w');
# 			fileWrite2 = open(dir+'trn-q'+str(qId)+'/condition.txt','w');
# 			prevId = qId;

'''
TODO: prepare these files: paths_wq_train.txt, paths_wq_test.txt
'''
#####################
### path.txt
### path_contains.txt
#####################
# predictedPathsFile = prefix+'Data/STAGG/preprocessed/paths_wq_train.txt';
# pathColumn = 3;
# weightcolumn = 4;
# with open(predictedPathsFile,'r') as f:
# 	prevId = -1;
# 	fileWrite = None;
# 	for line in f:
# 		tokens = line.split("\t");
# 		qId = int(tokens[qIDcolumn].strip());
# 		path = tokens[pathColumn];
# 		length = path.split(",");
# 		weight = 1.0;
# 		if len(tokens) > 4:
# 			weight = tokens[weightcolumn];
# 		if prevId == qId:
# 			relations = path.replace("/",".").split(",");
# 			fileWrite1.write("-".join(relations)+"\t"+str(weight)+"\n");
# 			for relation in relations:
# 				fileWrite2.write("-".join(relations)+"\t"+relation+"\t1.0\n");
# 		else:
# 			if fileWrite1:
# 				fileWrite1.close();
# 				fileWrite2.close();
# 			fileWrite1 = open(dir+'trn-q'+str(qId)+'/path.txt','w');
# 			fileWrite2 = open(dir+'trn-q'+str(qId)+'/path_contains.txt','w');

#####################
### rel.txt
#####################
# graph = Graph("/home/ASUAD/saditya1/Desktop/common/freebase2MDB");
# tx = g.begin();
# cypher = graph.cypher;
# for qId in range(0,questionNumbers):
# 	topicFile = open(dir+'trn-q'+str(qId)+'/topic.txt','r');
# 	fileWrite = open(dir+'trn-q'+str(qId)+'/rel.txt','w');
# 	for line in topicFile:
# 		tokens = line.split("\t");
# 		results = cypher.execute("MATCH p=(a {nodeId:\'"+tokens[0]+"\'})-[r]->(b) RETURN a.nodeId,type(r),b.nodeId");
# 		results.extend(cypher.execute("MATCH p=(a {nodeId:\'"+tokens[0]+"\'})<-[r]-(b) RETURN a.nodeId,type(r),b.nodeId"));
# 		for record in results:
# 			src = record['a.nodeId'];
# 			fileWrite.write(record[0]+"\t"+record[1]+"\t"+record[2]+"\n");
# 	fileWrite.close();
'''
	populate these files: outputNPsPathsTrainNew.txt (java)
'''
#####################
### condition_rel.txt
### condition_pair.txt
#####################
# SIMILAR_RELATIONS_THRESHOLD_P = 5;
# subquestionsFile = prefix + "Data/STAGG/preprocessed/outputNPsPathsTrainNew.txt";
# with open(subquestionsFile,'r') as f:
# 	for line in f:
# 		tokens = line.split("\t");
# 		qId = int(tokens[0].strip());
# 		fileWrite1 = open(dir+'trn-q'+str(qId)+'/condition_rel.txt','w');
# 		fileWrite2 = open(dir+'trn-q'+str(qId)+'/conditon_pair.txt','w');
# 		candidateEntities = tokens[2].split(";");
# 		candidateSubQuestions = tokens[4:];
# 		candEntityWeights = tokens[4].split(",");
# 		for i in range(0, len(candidateEntities)):
# 			results = cypher.execute("MATCH p=(a {nodeId:\'"+candidateEntities[i].strip()+"\'})-[r]-(b) RETURN type(r)");
# 			tuples = [];
# 			for record in results:
# 				tuples.add((record[0], getWord2VecSimilarity(candidateSubQuestions[i],record[0]) * candEntityWeights[i]));
# 			tuples = sorted(tuples, lambda x:x[1], reverse=True);
# 			for j in range(0,SIMILAR_RELATIONS_THRESHOLD_P):
# 				fileWrite1.write(tuples[j][0]+"\t"+tuples[j][1]+"\n");
# 				fileWrite2.write(candidateEntities[i]+"\t"+tuples[j][0]+"\t"+tuples[j][1]+"\n");
# 		fileWrite1.close();
# 		fileWrite2.close();

'''
TODO: Implement function getWord2VecSimilarity
'''
def getWord2VecSimilarity(subsentence, propertyString):
	raise NotImplementedError
