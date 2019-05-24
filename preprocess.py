import re
import pickle
import json

import lemmagen
from lemmagen.lemmatizer import Lemmatizer
from nltk.tokenize import RegexpTokenizer

import ufal_udpipe as udpipe

def remove_comments(corpus):
    regex = "\\((.*?)\\)"
    corpus['Questions'] = corpus['Questions'].apply(lambda x: re.sub(regex, '',
                                                                   x))
    corpus['Answers'] = corpus['Answers'].apply(lambda x: re.sub(regex, '', x))
    regex2 = "\\[(.*?)\\]"
    corpus['Questions'] = corpus['Questions'].apply(lambda x: re.sub(regex2,
                                                                   '', x))
    corpus['Answers'] = corpus['Answers'].apply(lambda x: re.sub(regex2, '', x))
    return corpus

def tokenize(corpus):
    tokenizer = RegexpTokenizer(r'\w+')
    return [[token.lower() for token in tokenizer.tokenize(doc)] for doc in
            corpus]

def remove_stopwords(tokens):
    stopwords = pickle.load(open('cache/stopwords.pkl', 'rb'))
    stopwords.append('um')
    return [[token for token in doc if token not in stopwords] for doc in tokens]

#temporary standardization
def standardize(tokens):
    slovar = pickle.load(open('cache/slovar.pkl', 'rb'))
    return [[slovar[token] if token in slovar else token for token in doc]
            for doc in tokens]

def lemmatize(tokens):
    lemmatizer = Lemmatizer(dictionary=lemmagen.DICTIONARY_SLOVENE)
    return [[lemmatizer.lemmatize(token) for token in doc] for doc in tokens]

def pos_tag(tokens):
    # noinspection PyTypeChecker
    model = udpipe.Model.load("model/slovenian-ssj-ud-2.3-181115.udpipe")
    output_format = udpipe.OutputFormat.newOutputFormat('epe')

    tagged_tokens = []

    for doc in tokens:
        temp_doc = []
        for token in doc:
            sentence = udpipe.Sentence()
            sentence.addWord(token)
            model.tag(sentence, model.DEFAULT)
            output = output_format.writeSentence(sentence)
            output = json.loads(output)
            temp_doc.append(
                (output["nodes"][0]["form"], output["nodes"][0]["properties"]["upos"]))
        tagged_tokens.append(temp_doc)
    return tagged_tokens

def make_dict():
    slovar = {}
    with open('utils/slovenian-colloquial-dict.txt', 'r') as f:
        for i in f.read().splitlines():
            slovar[i.split(', ')[0]] = i.split(', ')[1]
    pickle.dump(slovar, open('cache/slovar.pkl', 'wb'))

def make_stopwords():
    with open('utils/slovenian-stopwords.txt', 'r') as f:
        pickle.dump([i.strip(' ') for i in f.read().splitlines()],
                    open('cache/stopwords.pkl', 'wb'))

def preprocessing_pipeline(corpus):
    corpus = remove_comments(corpus)
    q_tokens = pos_tag(lemmatize(standardize(remove_stopwords(tokenize(
        corpus['Questions'])))))
    q_tokens = [[token for token, tag in doc if tag in ['NOUN', 'VERB']] for doc
              in q_tokens]
    a_tokens = pos_tag(lemmatize(standardize(remove_stopwords(tokenize(
        corpus['Answers'])))))
    a_tokens = [[token for token, tag in doc if tag in ['NOUN', 'VERB']] for doc
                in a_tokens]
    # tokens = [q + a for q, a in zip(q_tokens, a_tokens)]
    pickle.dump(q_tokens, open('cache/q_tokens.pkl', 'wb'))
    pickle.dump(a_tokens, open('cache/a_tokens.pkl', 'wb'))
    return corpus, q_tokens, a_tokens
