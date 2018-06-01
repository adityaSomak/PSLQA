from gensim import models
from pslplus.core import domain


def isnumeric(word):
    dWord = unicode(word,'utf-8')
    return dWord.isnumeric()

def calculateSimilarityOfWords(ruleT, headPredicates, bodypredicates):
    global word2vec_model
    if word2vec_model is None:
        loadW2VModel()
    wordsInBody = []
    for _,bPredicateList in bodypredicates.iteritems():
        for j in range(0, len(bPredicateList)):
            bPredicate = bPredicateList[j]
            args = bPredicate.args
            types = bPredicate.types
            for i in range(0,len(args)):
                if types[i]== domain.ArgumentType.STRING:
                    if not isnumeric(args[i]):
                        wordsInBody.append(args[i])
                    #if args[i] not in word2vec_model.vocab:
                    #    return 1.0
    wordsInHead =[]
    for _,hPred in headPredicates.iteritems():
        args = hPred.args
        types = hPred.types
        for i in range(0, len(args)):
            if types[i] == domain.ArgumentType.STRING:
                if not isnumeric(args[i]):
                    wordsInHead.append(args[i])
                #if args[i] not in word2vec_model.vocab:
                #    return 1.0
    if len(wordsInBody) <= 0 or len(wordsInHead) <= 0:
        return 1.0
    sim = 1.0
    try:
        sim = normalizeCosineSim(word2vec_model.n_similarity(wordsInBody,wordsInHead))
    except KeyError:
        return 1.0
    return sim

def normalizeCosineSim(sim):
    return (sim + 1.0) / 2.0

def similarityToAlistofWords(words, qWs):
    global word2vec_model
    if word2vec_model is None:
        loadW2VModel()
    try:
        return normalizeCosineSim(word2vec_model.n_similarity(words,qWs))
    except KeyError:
        return None

def loadConceptNetW2VModel():
    global cn_word2vec_model
    global cn_word2Index
    if cn_word2vec_model is not None:
        print "model already loaded ..."
        return
    WordVectors_File = "/windows/drive2/For PhD/KR Lab/DATASETS/embeddings/conceptnet-numberbatch-201609_en_word.txt"
    #WordVectors_File = "/data/somak/DATASETS/conceptnet-numberbatch-201609_en_word.txt"
    cn_word2vec_model = models.word2vec.Word2Vec.load_word2vec_format(WordVectors_File, binary=False)
    cn_word2vec_model.init_sims(replace=True)
    cn_word2Index = {}
    for i, k in enumerate(cn_word2vec_model.index2word):
        cn_word2Index[k] = i
    print "ConceptNet model loaded..."

def loadW2VModel():
    global word2vec_model
    global word2Index
    if word2vec_model is not None:
        print "model already loaded ..."
        return
    WordVectors_File = "/windows/drive2/For PhD/KR Lab/DATASETS/GoogleNews-vectors-negative300.bin"
    #WordVectors_File = "/data/somak/DATASETS/GoogleNews-vectors-negative300.bin"
    word2vec_model = models.word2vec.Word2Vec.load_word2vec_format(WordVectors_File, binary=True)
    word2vec_model.init_sims(replace=True)
    word2Index = {}
    for i, k in enumerate(word2vec_model.index2word):
        word2Index[k] = i
    print "word2vec model loaded..."

word2vec_model = None
word2Index = None

cn_word2vec_model = None
cn_word2Index = None
