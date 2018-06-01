import json
import collections

def getTrainingQAData(trainingDirectory, VQA=True):
    if VQA:
        answerJsonF = trainingDirectory+"/mscoco_train2014_annotations.json"
        questionJsonF = trainingDirectory+"Questions_Train_mscoco/OpenEnded_mscoco_train2014_questions.json"

        quesDict = {} # qid -> (question, image-id)
        imageDict = {} # imageid -> qid's
        with open(questionJsonF) as questionF:
            questions = json.load(questionF)
            for q in questions:
                quesDict[q['question_id']] = (str(q['question']),q['image_id'])
                imageDict[q['image_id']].setdefault([]).append(q['question_id'])

        answersDict = {} # qid -> answers
        with open(answerJsonF) as answerF:
            annotations = json.load(answerF)
            for ann in annotations:
                possibleAnswers =[]
                for ansJson in ann['answers']:
                    possibleAnswers.append(str(ansJson['answer']))
                answersDict[ann['question_id']] = possibleAnswers

        return QAData(quesDict,answersDict,imageDict)

    return None

def getTestQAData(testingDirectory, split='test', VQA=True):
    if VQA:
        if split == 'test':
            questionJsonF = testingDirectory+"OpenEnded_mscoco_test2015_questions.json"
        else:
            questionJsonF = testingDirectory + "OpenEnded_mscoco_val2014_questions.json"

        quesDict = {} # qid -> (question, image-id)
        imageDict = {} # imageid -> qid's
        count = 0
        with open(questionJsonF) as questionF:
            questions = json.load(questionF)
            for q in questions['questions']:
                quesDict[q['question_id']] = (str(q['question']),q['image_id'])
                try:
                    imageDict[q['image_id']].append(q['question_id'])
                except KeyError:
                    imageDict[q['image_id']]= [q['question_id']]
                count += 1

        answersDict = {} # qid -> answers

        return [QAData(quesDict,answersDict,imageDict), count]

    return None

def getAllPossibleAnswers(answerfile):
    answers = []
    with open(answerfile,'r') as ansFile:
        for line in ansFile:
            tokens = line.split("\t")
            if int(tokens[1]) > 10:
                answers.append(tokens[0])
    return answers[-1000:]

def getAnswerPriorsByQType(freqPriorJSon):
    with open(freqPriorJSon,'r') as freqPriorJSonF:
        typeDict = json.load(freqPriorJSonF)
    return typeDict

def getAnswersByType(top1000AnswersFile):
    answersByType = {}
    with open(top1000AnswersFile,'r') as ansFile:
        for line in ansFile:
            tokens = line.split("\t")
            types = map(lambda x: x.lower().strip(), tokens[2].split(","))
            for type in types:
                try:
                    answersByType[type].append(tokens[1].strip())
                except KeyError:
                    answersByType[type]= [tokens[1].strip()]
    return answersByType


def getAllPossibleAnswersAndRelevance(imgName, qaData):
    return [None, None]


def getQuestionsByImageName(imgName, qaData):
    imgName = imgName.split("_")[-1]
    imgId = imgName[:imgName.index(".jpg")].lstrip("0")
    qids = qaData.imageDict[int(str(imgId).strip())]
    questions = []
    for qid in qids:
        questions.append(Question(qid, qaData.questionsDict[qid][0]))
    return questions

def getMostProbableAnswerById(qid, qaData):
    answers = qaData.answersDict[qid]
    counts = collections.Counter(answers)
    new_list = sorted(answers, key=counts.get, reverse=True)
    return new_list[0]

class Question:
    def __init__(self, id, question):
        self.qid = id
        self.question = question

class QAData:

    def __init__(self, quesDict, answersDict, imageDict):
        # type: (object, object, object) -> object
        self.questionsDict = quesDict
        self.answersDict = answersDict
        self.imageDict = imageDict