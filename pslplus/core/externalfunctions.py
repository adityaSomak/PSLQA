from fuzzywuzzy import fuzz
from similarity import W2VPredicateSimilarity as w2v
from similarity import PhraseSimilarity

def getObjectType(args):
	return None;

def PathSimilar(*args):
	phrases = args[0][0]
	rWs = phrases[0].split(" ")
	pWs = phrases[1].split(" ")
	if w2v.word2vec_model is None:
		w2v.loadW2VModel()
	if w2v.cn_word2vec_model is None:
		w2v.loadConceptNetW2VModel()
	try:
		cnSim = PhraseSimilarity.similarity(phrases[0], phrases[1], True)
	except KeyError:
		cnSim = 0.0
	try:
		w2vSim = w2v.normalizeCosineSim(w2v.word2vec_model.n_similarity(rWs,pWs))
		if cnSim > 0.0:
			return 0.5*(cnSim + w2vSim)
		else:
			return w2vSim
	except KeyError:
		return 0.5

def SimilarPhrase(*args):
	global useWordNet
	phrases = args[0][0]
	rWs = phrases[0].split(" ")
	pWs = phrases[1].split(" ")
	if w2v.word2vec_model is None:
		w2v.loadW2VModel()
		wnSim = 0.0
	if useWordNet:
		wnSim = PhraseSimilarity.similarity(phrases[0], phrases[1], True)
		if wnSim is None:
			wnSim = 0.0
	try:
		w2vSim = w2v.normalizeCosineSim(w2v.word2vec_model.n_similarity(rWs,pWs))
		if wnSim > 0.0:
			return 0.5*(wnSim + w2vSim)
		else:
			return w2vSim
	except KeyError:
		return 0.5

def SimilarPhrases(*args):
	phrases = args[0][0]
	rWs = phrases[0].split(" ")
	relationWs = phrases[1].split(" ")
	relationWs.extend(phrases[2].split(" "))
	if w2v.word2vec_model is None:
		w2v.loadW2VModel()
	try:
		return w2v.normalizeCosineSim(w2v.word2vec_model.n_similarity(rWs,relationWs))
	except KeyError:
		return 0.5

def SameName(*args):
	names = args[0][0]
	return fuzz.ratio(names[0],names[1])/100.0


def evaluate(functionname,*args):
	if functionname.startswith("Fn_"):
		functionname = functionname[3:]
	return allFunctions[functionname](args)


useWordNet = False
allFunctions = {}
allFunctions['SameName'] = SameName
allFunctions['SimilarPhrase'] = SimilarPhrase
allFunctions['PathSimilar'] = PathSimilar
allFunctions['SimilarPhrases'] = SimilarPhrases
#print evaluate(allFunctions['SameName'],("hello","hilo","hi"))
